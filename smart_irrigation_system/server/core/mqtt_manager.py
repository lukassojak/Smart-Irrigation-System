import json
import threading
import paho.mqtt.client as mqtt
from smart_irrigation_system.server.utils.logger import get_logger

class MQTTManager(threading.Thread):
    def __init__(self, node_registry, broker_host="localhost", broker_port=1883):
        super().__init__(daemon=True)
        self.logger = get_logger("MQTTManager")
        self.node_registry = node_registry
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client(client_id="server_mqtt_manager")
        self._stop_event = threading.Event()

        # MQTT callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Connected to MQTT broker.")
            self.client.subscribe("irrigation/+/status")
        else:
            self.logger.error(f"MQTT connection failed with code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            node_id = msg.topic.split("/")[1]
            self.logger.debug(f"Received status from {node_id}: {payload}")
            self.node_registry.update_node_status(node_id, payload)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    # ------------------- Public methods ------------------- #

    def publish_command(self, node_id: str, command: dict):
        """Publish a command to a specific irrigation node."""
        topic = f"irrigation/{node_id}/command"
        self.client.publish(topic, json.dumps(command))
        self.logger.info(f"Command published to {topic}: {command}")

    def run(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return

        self.client.loop_start()
        self.logger.info("MQTT loop started.")
        while not self._stop_event.is_set():
            self._stop_event.wait(1)
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("MQTT client stopped.")

    def stop(self):
        self._stop_event.set()
