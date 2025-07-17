from smart_irrigation_system.irrigation_controller import IrrigationController
from smart_irrigation_system.enums import Environment

ENVIRONMENT = Environment.PC


# This is the main file that will be run on the Raspberry Pi.



def main():
    controller = IrrigationController()


    # Perform irrigation
    controller.perform_irrigation_sequential()

if __name__ == "__main__":
    main()