# smart_irrigation_system/server/core/server_core.py

import threading, os
from smart_irrigation_system.server.core.mqtt_manager import MQTTManager
from smart_irrigation_system.server.core.node_registry import NodeRegistry, parse_node_status
from smart_irrigation_system.server.core.node_topology_service import NodeTopologyService
from smart_irrigation_system.server.utils.logger import get_logger


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../.."))

NODES_STATE_DIR = os.path.join(BASE_DIR, "runtime", "server", "data")
NODES_STATE_FILE = os.path.join(NODES_STATE_DIR, "nodes_state.json")

CONFIG_DIR = os.path.join(BASE_DIR, "runtime", "server", "config")

PERIODIC_STATUS_UPDATE_INTERVAL = 10  # seconds


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

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

    def __init__(self, broker_host: str | None = None, broker_port: int | None = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        resolved_broker_host = broker_host or os.getenv("MQTT_HOST", "localhost")
        resolved_broker_port = int(broker_port or os.getenv("MQTT_PORT", "1883"))

        self.logger = get_logger("IrrigationServer")
        self.node_registry = NodeRegistry(file_path=NODES_STATE_FILE)
        self.mqtt_manager = MQTTManager(self.node_registry, resolved_broker_host, resolved_broker_port)
        self.node_topology_service = NodeTopologyService()
        self.enable_status_polling = _env_bool("MQTT_ENABLE_STATUS_POLLING", default=False)
        self.status_polling_interval_seconds = int(
            os.getenv("MQTT_STATUS_POLL_INTERVAL_SECONDS", str(PERIODIC_STATUS_UPDATE_INTERVAL))
        )
        self._running = False

    def get_node_summary(self):
        nodes = self.node_registry.nodes
        parsed_nodes = {}

        for node_id, data in nodes.items():
            raw_status = data.get("last_status")
            parsed_nodes[node_id] = {
                **data,
                "status": parse_node_status(raw_status)
            }
        return parsed_nodes


    def update_all_node_statuses(self):
        for node_id in self.node_topology_service.get_all_node_ids():
            command = {"action": "get_status"}
            self.mqtt_manager.publish_command(node_id, command)

    def start(self):
        self.logger.info("Starting Irrigation Server...")
        self.mqtt_manager.start()
        self._running = True
        if self.enable_status_polling:
            self.periodic_status_update(self.status_polling_interval_seconds)
            self.logger.info(
                "MQTT status polling enabled (interval=%ss).",
                self.status_polling_interval_seconds,
            )
        else:
            self.logger.info("MQTT status polling disabled. Using node push snapshots and on-demand status requests.")
        self.logger.info("Server started successfully.")

    def stop(self):
        if not self._running:
            return
        self.logger.info("Stopping Irrigation Server...")
        self.mqtt_manager.stop()
        self.mqtt_manager.join(timeout=3)
        self._running = False
        self.logger.info("Server stopped.")

    def stop_all_irrigation(self):
        for node_id in self.node_topology_service.get_all_node_ids():
            command = {"action": "stop_irrigation"}
            self.mqtt_manager.publish_command(node_id, command)
    
    def periodic_status_update(self, interval_seconds=10):
        """Periodically request status updates from all nodes."""
        def _update_loop():
            while self._running:
                self.update_all_node_statuses()
                threading.Event().wait(interval_seconds)
        
        threading.Thread(target=_update_loop, daemon=True).start()
