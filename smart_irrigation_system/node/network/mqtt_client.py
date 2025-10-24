import json
import threading
import time
import paho.mqtt.client as mqtt

from smart_irrigation_system.node.utils.logger import get_logger


class MQTTClient(threading.Thread):
    def __init__(self, handler, node_id="node1", broker_host="localhost", broker_port=1883):
        super().__init__(daemon=True)
        self.handler = handler
        self.node_id = node_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client(client_id=f"irrigation_{node_id}")
        self.logger = get_logger("MQTTClient")
        self._stop_event = threading.Event()

        # Assign MQTT callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.logger.info(f"MQTTClient initialized for node_id={node_id}, broker={broker_host}:{broker_port}")


    # MQTT callbacks
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            topic = f"irrigation/{self.node_id}/command"
            self.logger.info(f"Connected to broker. Subscribing to {topic}")
            client.subscribe(topic)
        else:
            self.logger.error(f"MQTT connection failed with code {rc}")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        self.logger.debug(f"Received message on {msg.topic}: {payload}")
        self.handler.handle(payload)

    # Publisher helper
    def publish_status(self, payload: dict):
        topic = f"irrigation/{self.node_id}/status"
        self.client.publish(topic, json.dumps(payload))
        self.logger.debug(f"Published status to {topic}")

    # Thread main loop
    def run(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            # Future: implement reconnection logic
            return

        self.client.loop_start()
        self.logger.info("MQTT loop started.")
        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("MQTT client stopped.")

    def stop(self):
        self._stop_event.set()
