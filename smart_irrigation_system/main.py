from smart_irrigation_system.irrigation_controller import IrrigationController
from smart_irrigation_system.enums import Environment
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.button import Button
# import atexit, os - for cleanup and unclean shutdown logging

ENVIRONMENT = Environment.PC


# This is the main file that will be run on the Raspberry Pi.



def main():
    """Main function to start the Smart Irrigation System."""
    logger = get_logger("smart_irrigation_system.main")
    logger.info("Initializing Smart Irrigation System...")
    controller = IrrigationController()
    logger.info("Starting Smart Irrigation System on %s environment", ENVIRONMENT.name)


    # Perform irrigation
    logger.info("Starting irrigation process...")
    print("")
    controller.perform_irrigation_sequential()
    print("")
    logger.info("Irrigation process completed successfully.")

if __name__ == "__main__":
    main()