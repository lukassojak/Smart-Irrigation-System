# tracemalloc - for debugging performance issues
import tracemalloc
import threading

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
CHECK_INTERVAL = 10
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




def command_loop(controller: IrrigationController, stop_event):
    print("Command interface ready. Type 'help' for options.")
    while True:
        try:
            cmd = input(">> ").strip().lower()
            if cmd in ("exit", "quit"):
                logger.info("Shutting down Smart Irrigation System...")
                print("Shutting down Smart Irrigation System...")
                if controller.get_state() == ControllerState.IRRIGATING:
                    print("Stopping irrigation before exiting...")
                    controller.stop_irrigation()
                stop_event.set()  # Signal the main loop to stop
                break
            elif cmd == "help":
                print("Available commands:")
                print("  irrigate     - start sequential irrigation")
                print("  pause        - pause irrigation system")
                print("  resume       - resume irrigation system")
                print("  stop         - stop all irrigation")
                print("  open valves  - open all valves")
                print("  close valves - close all valves")
                print("  state        - print controller state")
                print("  quit/exit    - quit CLI and shutdown system")
            elif cmd == "irrigate":
                print("Starting sequential irrigation...")
                controller.start_automatic_irrigation()
                timeout = 20 # Wait for irrigation to start
                while controller.get_state() != ControllerState.IRRIGATING:
                    if timeout <= 0:
                        print("Irrigation unable to start. Check zones configuration.")
                        break
                    time.sleep(1)
                    timeout -= 1
                print("Controller state:", controller.get_state().name)
            elif cmd == "stop":
                print("Stopping all irrigation...")
                controller.stop_irrigation()
                while controller.get_state() == ControllerState.IRRIGATING:
                    time.sleep(1)
                print("Controller state:", controller.get_state().name)
            elif cmd == "state":
                print(f"Controller state: {controller.get_state().name}")
            elif cmd == "pause":
                if paused:
                    print("System is already paused. Type 'resume' to continue.")
                else:
                    toggle_pause(True)
                    print("System paused. Type 'resume' to continue.")
            elif cmd == "resume":
                if not paused:
                    print("System is not paused. Type 'pause' to pause.")
                else:
                    toggle_pause(False)
                    print("System resumed.")
            elif cmd == "open valves":
                controller.open_valves()
                print("All valves opened.")
            elif cmd == "close valves":
                controller.close_valves()
                print("All valves closed.")
            else:
                print("Unknown command. Type 'help'.")
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Shutting down...")
            logger.info("Keyboard interrupt received. Shutting down...")
            controller.stop_irrigation()
            stop_event.set()  # Signal the main loop to stop
        except Exception as e:
            logger.error(f"Error in command loop: {e}")




def main_loop(controller, display, pause_button, daily_irrigation_time, stop_event):
    """Main loop for the Smart Irrigation System."""
    irrigation_hour = daily_irrigation_time.tm_hour
    irrigation_minute = daily_irrigation_time.tm_min
    
    try:
        while not stop_event.is_set():
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
            if (current_hour == irrigation_hour and 
                abs(current_minute - irrigation_minute) <= TOLERANCE):
                logger.debug(f"Current time {current_time_str} matches irrigation time {irrigation_hour:02}:{irrigation_minute:02} within tolerance of {TOLERANCE} minutes.")
                display.render()
                controller.start_automatic_irrigation()
                while controller.get_state() == ControllerState.IRRIGATING:
                    # Wait until irrigation is done
                    time.sleep(CHECK_INTERVAL)
            else:
                time_left = (irrigation_hour - current_hour) * 60 + (irrigation_minute - current_minute)
                if time_left < 0:
                    time_left += 24 * 60
                display.render()

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Exiting...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

def main():
    """Main function to start the Smart Irrigation System."""
    tracemalloc.start()
    logger.info("Initializing Smart Irrigation System...")

    try:
        controller = IrrigationController()
    except Exception as e:
        logger.error(f"Failed to initialize IrrigationController: {e}")
        return

    display = DisplayController(controller)
    pause_button = Button(gpio_pin=17, led_pin=27, user_callback=toggle_pause)
    logger.info("Starting Smart Irrigation System on %s environment.", ENVIRONMENT.name)

    daily_irrigation_time: time.struct_time = controller.get_daily_irrigation_time()
    stop_event = threading.Event()

    # Start the main loop in a separate thread
    loop_thread = threading.Thread(
        target=main_loop,
        args=(controller, display, pause_button, daily_irrigation_time, stop_event),
        daemon=True
    )
    loop_thread.start()

    # Start CLI in the main thread
    command_loop(controller, stop_event)

    # Wait for the main loop to finish
    loop_thread.join()

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