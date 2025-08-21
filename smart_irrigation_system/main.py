# tracemalloc - for debugging performance issues
import tracemalloc

from smart_irrigation_system.irrigation_controller import IrrigationController
from smart_irrigation_system.enums import Environment
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.button import Button
from smart_irrigation_system.display_controller import DisplayController
from smart_irrigation_system.enums import ControllerState
from smart_irrigation_system.irrigation_cli import IrrigationCLI


# import atexit, os - for cleanup and unclean shutdown logging
import time
# import machine


# === Configuration ===
CHECK_INTERVAL = 10
I2C_SCL = 5  # GPIO pin for I2C SCL
I2C_SDA = 4  # GPIO pin for I2C SDA

# === Constants ===
TOLERANCE = 1  # Tolerance in minutes for irrigation time

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

    # Start the controller main loop
    controller.start_main_loop()

    # Start CLI in the main thread
    # command_loop(controller, stop_event)
    cli = IrrigationCLI(controller, refresh_interval=0.05)
    cli.run()

    controller.stop_main_loop()

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