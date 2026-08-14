# tracemalloc - for debugging performance issues
import tracemalloc, time

from smart_irrigation_system.__version__ import __version__ as version
from smart_irrigation_system.node.utils.logger import get_logger
from smart_irrigation_system.node.config.identity import load_node_identity
from smart_irrigation_system.node.network.mqtt_client import MQTTClient

from smart_irrigation_system.node.core.controller.controller_core import ControllerCore


# === Constants ===
REFRESH_INTERVAL_IDLE = 0.5  # Refresh interval for the CLI in seconds when idle
REFRESH_INTERVAL_ACTIVE = 0.1  # Refresh interval for the CLI in seconds when active

# === Global Variables ===
logger = get_logger("smart_irrigation_system.main")

def main():
    """Main function to start the Smart Irrigation Node."""
    tracemalloc.start()
    logger.info("Initializing Smart Irrigation Node...")
    logger.info(f"Version: {version}")
    print("Initializing ...", flush=True)

    # Initialize the ControllerCore
    try:
        controller = ControllerCore()
    except Exception as e:
        logger.error(f"Failed to initialize ControllerCore: {e}")
        return

    # Initialize network components
    try:
        identity = load_node_identity()
        mqtt_client = MQTTClient(controller, identity=identity)
        mqtt_client.start()
    except Exception as e:
        logger.error(f"Failed to initialize network components: {e}")
        del controller
        return

    print("Smart Irrigation Node is running. Press Ctrl+C to exit.", flush=True)
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting Smart Irrigation System...")
    finally:
        mqtt_client.stop()
        del controller
        logger.info("Smart Irrigation System stopped.")

    # Debug memory usage
    current, peak = tracemalloc.get_traced_memory()
    current_kb = current / 1024
    peak_kb = peak / 1024
    logger.debug(f"Current memory usage: {current_kb:.2f} KB; Peak: {peak_kb:.2f} KB")
    tracemalloc.stop()


if __name__ == "__main__":
    main()