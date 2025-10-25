import threading, os
from smart_irrigation_system.server.core.mqtt_manager import MQTTManager
from smart_irrigation_system.server.core.node_registry import NodeRegistry
from smart_irrigation_system.server.core.zone_node_mapper import ZoneNodeMapper
from smart_irrigation_system.server.utils.logger import get_logger


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../.."))

NODES_STATE_DIR = os.path.join(BASE_DIR, "runtime", "server", "data")
NODES_STATE_FILE = os.path.join(NODES_STATE_DIR, "nodes_state.json")

CONFIG_DIR = os.path.join(BASE_DIR, "runtime", "server", "config")

class IrrigationServer:
    """Central orchestrator for the Smart Irrigation Server."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton implementation"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, broker_host="localhost", broker_port=1883):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self.logger = get_logger("IrrigationServer")
        self.node_registry = NodeRegistry(file_path=NODES_STATE_FILE)
        self.mqtt_manager = MQTTManager(self.node_registry, broker_host, broker_port)
        self.zone_node_mapper = ZoneNodeMapper()
        self._running = False

    def start(self):
        self.logger.info("Starting Irrigation Server...")
        self.mqtt_manager.start()
        self._running = True
        self.logger.info("Server started successfully.")

    def stop(self):
        if not self._running:
            return
        self.logger.info("Stopping Irrigation Server...")
        self.mqtt_manager.stop()
        self.mqtt_manager.join(timeout=3)
        self._running = False
        self.logger.info("Server stopped.")

    def get_node_summary(self):
        return self.node_registry.nodes
    
    def update_all_node_statuses(self):
        for node_id in self.zone_node_mapper.get_all_node_ids():
            command = {"action": "get_status"}
            self.mqtt_manager.publish_command(node_id, command)

    def stop_all_irrigation(self):
        for node_id in self.zone_node_mapper.get_all_node_ids():
            command = {"action": "stop_irrigation"}
            self.mqtt_manager.publish_command(node_id, command)
