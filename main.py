import time
from irrigation_controller import IrrigationController
from global_conditions import GlobalConditions



# This is the main file that will be run on the Raspberry Pi Pico



def main():
    controller = IrrigationController()

    # Add circuits
    controller.add_circuit("Front Yard", 0, [(1, 2)])           # Circuit 0, with relay pin 0, and sensors on pins 1 and 2
    controller.add_circuit("Back Yard", 3, [(4, 5), (6, 7)])    # Circuit 1, with relay pin 3, and sensors on pins 4, 5, 6, and 7
    controller.add_circuit("Garden", 8, [])                     # Circuit 2, with relay pin 8, and no sensors

    # Print the current global conditions
    controller.print_conditions()

    # Perform irrigation
    controller.perform_irrigation()

    # Simulate interruption after 2 seconds
    time.sleep(2)
    controller.stop_irrigation()


if __name__ == "__main__":
    main()