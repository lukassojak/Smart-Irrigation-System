# tracemalloc - for debugging performance issues
import tracemalloc, time

from smart_irrigation_system.__version__ import __version__ as version
from smart_irrigation_system.node.core.irrigation_controller import IrrigationController
from smart_irrigation_system.node.core.enums import Environment
from smart_irrigation_system.node.utils.logger import get_logger
from smart_irrigation_system.node.interface.button import Button
from smart_irrigation_system.node.interface.display_controller import DisplayController
from smart_irrigation_system.node.core.enums import ControllerState
from smart_irrigation_system.node.interface.irrigation_cli import IrrigationCLI
from smart_irrigation_system.node.network.mqtt_client import MQTTClient
from smart_irrigation_system.node.network.server_command_handler import ServerCommandHandler

from smart_irrigation_system.node.core.controller.controller_core import ControllerCore


# === Configuration ===
I2C_SCL = 5  # GPIO pin for I2C SCL
I2C_SDA = 4  # GPIO pin for I2C SDA

# === Constants ===
REFRESH_INTERVAL_IDLE = 0.5  # Refresh interval for the CLI in seconds when idle
REFRESH_INTERVAL_ACTIVE = 0.1  # Refresh interval for the CLI in seconds when active

# === Global Variables ===
logger = get_logger("smart_irrigation_system.main")

# Callback function to toggle pause state
def toggle_pause(state):
    global paused
    paused = state
    if paused:
        logger.info("Irrigation system paused.")
    else:
        logger.info("Irrigation system resumed.")


def main():
    """Main function to start the Smart Irrigation Node."""
    tracemalloc.start()
    logger.info("Initializing Smart Irrigation Node...")
    logger.info(f"Version: {version}")
    print("Initializing ", end="", flush=True)
    time.sleep(0.5)
    print(".", end="", flush=True)

    # Initialize the Irrigation Controller
    try:
        controller = ControllerCore()
        time.sleep(0.5)
        print(".", end="", flush=True)
    except Exception as e:
        logger.error(f"Failed to initialize IrrigationController: {e}")
        return

    # Initialize network components
    try:
        server_command_handler = ServerCommandHandler(controller, None) # MQTTClient will be set after its creation
        mqtt_client = MQTTClient(server_command_handler, node_id="node1", broker_host="localhost", broker_port=1883)
        server_command_handler.mqtt_client = mqtt_client  # Set the mqtt_client in the handler
        mqtt_client.start()
        time.sleep(0.5)
        print(".", end="", flush=True)
    except Exception as e:
        logger.error(f"Failed to initialize network components: {e}")
        del controller
        return

    # Start the controller main loop
    controller.start_main_loop()

    # Initialize CLI
    try:
        cli = IrrigationCLI(controller, refresh_interval_idle=REFRESH_INTERVAL_IDLE,
                            refresh_interval_active=REFRESH_INTERVAL_ACTIVE)
    except Exception as e:
        logger.error(f"Failed to initialize IrrigationCLI: {e}")
        controller.stop_main_loop()
        del controller
        return
    
    # Run the CLI
    try:
        cli.run()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting Smart Irrigation System...")
    except Exception as e:
        logger.error(f"Error in CLI: {e}")

    controller.stop_main_loop()

    # Finalize controller
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