import json
import re
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
                "last_update": datetime.now().strftime("%Y-%m-%dT%H:%M:%S") # in future, use UTC time format
            }
            with open(self.file_path, "w") as f:
                json.dump(self.nodes, f, indent=2)
        self.logger.debug(f"Updated node {node_id} status.")


def parse_node_status(raw_status: str) -> dict | None:
    """
    Parse raw status message from node into structured dictionary.

    Example input:
        "Controller State: IRRIGATING, Auto Enabled: True, Auto Paused: True, Currently Irrigating Zones: [1, 2]"

    Output:
        {
            "controller_state": "IRRIGATING",
            "auto_enabled": True,
            "auto_paused": True,
            "zones": [1, 2]
        }
    """
    if not raw_status or not isinstance(raw_status, str):
        return None

    # Remove surrounding quotes and whitespace
    raw = raw_status.strip().strip('"').strip()

    try:
        # REGEX for parsing
        controller_match = re.search(r"Controller State:\s*([A-Za-z_]+)", raw)
        auto_enabled_match = re.search(r"Auto Enabled:\s*(True|False)", raw)
        auto_paused_match = re.search(r"Auto Paused:\s*(True|False)", raw)
        zones_match = re.search(r"Currently Irrigating Zones:\s*\[([^\]]*)\]", raw)

        controller_state = controller_match.group(1) if controller_match else None
        auto_enabled = (
            auto_enabled_match.group(1).lower() == "true" if auto_enabled_match else None
        )
        auto_paused = (
            auto_paused_match.group(1).lower() == "true" if auto_paused_match else None
        )

        # Zones parsing - convert to list of integers
        zones_raw = zones_match.group(1).strip() if zones_match else ""
        if zones_raw:
            try:
                zones = [int(x.strip()) for x in zones_raw.split(",") if x.strip()]
            except ValueError:
                zones = []
        else:
            zones = []

        return {
            "controller_state": controller_state,
            "auto_enabled": auto_enabled,
            "auto_paused": auto_paused,
            "zones": zones,
        }

    except Exception as e:
        # If parsing fails, return None
        return None
