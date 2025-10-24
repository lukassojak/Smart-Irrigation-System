import json

from smart_irrigation_system.node.core.irrigation_controller import IrrigationController
from smart_irrigation_system.node.network.mqtt_client import MQTTClient
from smart_irrigation_system.node.utils.logger import get_logger


class ServerCommandHandler:
    def __init__(self, irrigation_controller: IrrigationController, mqtt_client: MQTTClient):
        self.irrigation_controller = irrigation_controller
        self.mqtt_client = mqtt_client
        self.logger = get_logger("ServerCommandHandler")

    def handle(self, message: str):
        """Process incoming mqtt message (JSON)."""
        # Future improvements: registry pattern for commands (map action to method)
        try:
            cmd = json.loads(message)
            action = cmd.get("action")

            if action == "get_status":
                self._publish_status()
            elif action == "start_irrigation":
                self._start_irrigation(cmd)
            elif action == "stop_irrigation":
                self.irrigation_controller.stop_irrigation()
            else:
                self.logger.warning(f"Unknown command action: {action}")

        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON message")
        except Exception as e:
            self.logger.error(f"Error handling server command: {e}")

    # ------------------- Private methods ------------------- #
    
    def _publish_status(self):
        """Publish current irrigation system status to server."""
        status = self.irrigation_controller.get_status_message()
        self.mqtt_client.publish_status(status)
        self.logger.debug("Published current status to server.")
    
    def _start_irrigation(self, cmd):
        """Start manual irrigation for a specific zone and amount."""
        try:
            zone_id = int(cmd.get("zone_id"))
            liter_amount = float(cmd.get("liter_amount"))
        except (TypeError, ValueError):
            self.logger.error(f"Invalid parameters in start_irrigation command: {cmd}")
            return

        self.logger.info(f"Requested manual irrigation: zone_id={zone_id}, liter_amount={liter_amount}")
        self.irrigation_controller.manual_irrigation(zone_id, liter_amount)