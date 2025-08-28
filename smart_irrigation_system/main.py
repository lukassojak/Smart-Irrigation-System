# tracemalloc - for debugging performance issues
import tracemalloc

from smart_irrigation_system.__version__ import __version__ as version
from smart_irrigation_system.irrigation_controller import IrrigationController
from smart_irrigation_system.enums import Environment
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.button import Button
from smart_irrigation_system.display_controller import DisplayController
from smart_irrigation_system.enums import ControllerState
from smart_irrigation_system.irrigation_cli import IrrigationCLI


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
    """Main function to start the Smart Irrigation System."""
    tracemalloc.start()
    logger.info("Initializing Smart Irrigation System...")
    logger.info(f"Version: {version}")

    try:
        controller = IrrigationController()
    except Exception as e:
        logger.error(f"Failed to initialize IrrigationController: {e}")
        return

    # display = DisplayController(controller)
    # pause_button = Button(gpio_pin=17, led_pin=27, user_callback=toggle_pause)

    # Start the controller main loop
    controller.start_main_loop()

    # Start CLI in the main thread
    # command_loop(controller, stop_event)
    cli = IrrigationCLI(controller, refresh_interval_idle=REFRESH_INTERVAL_IDLE,
                        refresh_interval_active=REFRESH_INTERVAL_ACTIVE)
    cli.run()

    controller.stop_main_loop()

    # Cleanup resources
    controller.cleanup()
    # display.cleanup()
    # pause_button.cleanup()
    logger.info("Smart Irrigation System stopped.")

    current, peak = tracemalloc.get_traced_memory()
    current_kb = current / 1024
    peak_kb = peak / 1024
    logger.debug(f"Current memory usage: {current_kb:.2f} KB; Peak: {peak_kb:.2f} KB")
    tracemalloc.stop()


if __name__ == "__main__":
    main()