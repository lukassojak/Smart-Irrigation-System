# tracemalloc - for debugging performance issues
import tracemalloc

from smart_irrigation_system.irrigation_controller import IrrigationController
from smart_irrigation_system.enums import Environment
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.button import Button
from smart_irrigation_system.display_controller import DisplayController
from smart_irrigation_system.enums import ControllerState


# import atexit, os - for cleanup and unclean shutdown logging
import time
# import machine


# === Configuration ===
CHECK_INTERVAL = 30
I2C_SCL = 5  # GPIO pin for I2C SCL
I2C_SDA = 4  # GPIO pin for I2C SDA

# === Constants ===
TOLERANCE = 1  # Tolerance in minutes for irrigation time
ENVIRONMENT = Environment.PC

# === Global Variables ===
logger = get_logger("smart_irrigation_system.main")
paused = False  # Global variable to track pause state


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
    
    # === Initialization ===

    logger.info("Initializing Smart Irrigation System...")
    try:
        controller = IrrigationController()
    except Exception as e:
        logger.error(f"Failed to initialize IrrigationController: {e}")
        return

    display = DisplayController(controller)
    pause_button = Button(gpio_pin=17, led_pin=27, user_callback=toggle_pause)
    logger.info("Starting Smart Irrigation System on %s environment", ENVIRONMENT.name)

    daily_irrigation_time: time.struct_time = controller.get_daily_irrigation_time()
    irrigation_hour = daily_irrigation_time.tm_hour
    irrigation_minute = daily_irrigation_time.tm_min

    # === Main Loop ===
    try:
        while True:
            if controller.get_state() == ControllerState.IRRIGATING:
                # If irrigating, just update the display and wait
                display.render()
                time.sleep(CHECK_INTERVAL)
                continue
            if paused:
                logger.info("System is paused. Waiting for resume...")
                # If paused, just update the display and wait
                display.render()
                time.sleep(CHECK_INTERVAL)
                continue
            # Check if it's time to irrigate
            current_hour = time.localtime().tm_hour
            current_minute = time.localtime().tm_min
            # format current time for logging
            current_time_str = f"{current_hour:02}:{current_minute:02}"
            logger.debug(f"Evaluating irrigation time. Current time: {current_time_str}, ")
            if (current_hour == irrigation_hour and 
                abs(current_minute - irrigation_minute) <= TOLERANCE):
                logger.debug(f"Current time {current_time_str} matches irrigation time {irrigation_hour:02}:{irrigation_minute:02} within tolerance of {TOLERANCE} minutes.")
                display.render()
                controller.perform_automatic_irrigation()
                time.sleep(TOLERANCE + CHECK_INTERVAL)  # Wait for TOLERANCE + CHECK_INTERVAL to avoid multiple triggers
            else:
                time_left = (irrigation_hour - current_hour) * 60 + (irrigation_minute - current_minute)
                if time_left < 0:
                    time_left += 24 * 60
                logger.debug(f"Next irrigation in {time_left} minutes.")
                display.render()

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Exiting...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        # Cleanup resources
        controller.cleanup()
        display.cleanup()
        pause_button.cleanup()
        logger.info("Smart Irrigation System stopped.")

        current, peak = tracemalloc.get_traced_memory()
        current_kb = current / 1024
        peak_kb = peak / 1024
        logger.debug(f"Current memory usage: {current_kb:.2f} KB; Peak: {peak_kb:.2f} KB")
        tracemalloc.stop()


if __name__ == "__main__":
    main()