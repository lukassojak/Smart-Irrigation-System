import json
import threading
from datetime import datetime
from smart_irrigation_system.server.utils.logger import get_logger

class NodeRegistry:
    def __init__(self, file_path):
        self.file_path = file_path
        self.logger = get_logger("NodeRegistry")
        self.lock = threading.Lock()
        self.nodes = self._load_nodes()

    def _load_nodes(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("nodes_state.json not found, starting with empty registry.")
            return {}
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON in nodes_state.json, resetting.")
            return {}

    def update_node_status(self, node_id, status_message):
        with self.lock:
            self.nodes[node_id] = {
                "last_status": status_message,
                "last_update": datetime.now().replace(microsecond=0)
            }
            with open(self.file_path, "w") as f:
                json.dump(self.nodes, f, indent=2)
        self.logger.debug(f"Updated node {node_id} status.")
