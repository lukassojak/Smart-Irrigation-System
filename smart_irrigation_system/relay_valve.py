try:
    import RPi.GPIO as GPIO
    GPIO_SUPPORTED = True
# if ImportError or RuntimeError occurs, we will use a dummy GPIO class for testing
except (ImportError, RuntimeError):
    GPIO_SUPPORTED = False
    class GPIO:
        BCM = None
        IN = None
        OUT = None
        PUD_UP = None
        LOW = None
        HIGH = None
        FALLING = None
        RISING = None
        BOTH = None
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode, pull_up_down=None): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def input(pin): return False
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None): pass
        @staticmethod
        def cleanup(pins=None): pass
    
    GPIO = GPIO  # Use the dummy GPIO class for testing



import time
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.enums import RelayValveState
from typing import Optional


TOLERANCE = 0.5  # Tolerance for time checks, in seconds


class RelayValve:
    def __init__(self, pin):
        # Initialize the relay valve logger with a specific pin number
        self.logger = get_logger(f"RelayValve-{pin}")
        self.pin = pin
        
        # Initialize GPIO pin for the relay valve
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)  # Set the pin as an output
        GPIO.output(self.pin, GPIO.LOW)  # Ensure the valve is closed initially

        self.state = RelayValveState.CLOSED  # Default state is CLOSED
        self.logger.info(f"RelayValve initialized on pin {self.pin}")

    def get_state(self) -> RelayValveState:
        """Returns the current state of the relay valve"""
        return self.state


    def control(self, new_state: RelayValveState) -> None:
        """Enables or disables the relay valve to start or stop watering"""
        MAX_RETRIES = 3  # Maximum number of retries for state change
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                if new_state == RelayValveState.OPEN:
                    if self.state == RelayValveState.OPEN:
                        self.logger.warning(f"Valve {self.pin} is already OPEN, no action taken.")
                        return
                    
                    GPIO.output(self.pin, GPIO.HIGH)  # Set the pin to HIGH to open the valve

                    self.state = RelayValveState.OPEN
                    self.logger.debug(f"RelayValve state changed to OPEN on pin {self.pin}")
                    return
                else:
                    if self.state == RelayValveState.CLOSED:
                        self.logger.warning(f"Valve {self.pin} is already CLOSED, no action taken.")
                        return
                    
                    GPIO.output(self.pin, GPIO.LOW)  # Set the pin to LOW to close the valve
    
                    self.state = RelayValveState.CLOSED
                    self.logger.debug(f"RelayValve state changed to CLOSED on pin {self.pin}")
                    return  # Exit the loop after successful state change
                
            except RuntimeError as e:
                time.sleep(1)  # Wait before retrying
                retry_count += 1
                self.logger.error(f"Runtime error while controlling valve: {e}. Retrying ({retry_count}/{MAX_RETRIES})...")

            except Exception as e:
                self.logger.error(f"Unexpected error while controlling valve: {e}")
                time.sleep(1)  # Wait before retrying
                retry_count += 1

        # If all retries fail and valve cannot be CLOSED, log a critical error and raise an exception
        if self.state == RelayValveState.OPEN:
            self.logger.critical(f"Failed to close valve {self.pin} after {MAX_RETRIES} retries. Please check the hardware.")
            raise Exception(f"Failed to close valve {self.pin} after {MAX_RETRIES} retries. Please check the hardware.")
        else:
            self.logger.error(f"Failed to open valve {self.pin} after {MAX_RETRIES} retries. Please check the hardware.")
            raise Exception(f"Failed to open valve {self.pin} after {MAX_RETRIES} retries. Please check the hardware.")


    def open(self, duration, stop_event) -> Optional[int]:
        """Opens the valve for a specified duration. Returns the duration in seconds if successful, or raises an exception if the valve is closed early."""

        self.logger.debug(f"Valve will be opened for {duration} seconds.")
        self.control(RelayValveState.OPEN)
    
        # try-except block provides a fail-safe mechanism to ensure the valve is not left open indefinitely
        try:
            start_time = time.time()
            elapsed_time = 0
            while time.time() - start_time < duration:
                elapsed_time = time.time() - start_time
                if stop_event.is_set():
                    self.logger.info(f"Closing valve early due to stop event after {time.time() - start_time:.0f} seconds")
                    # return elapsed time if the stop event is triggered
                    return int(elapsed_time)

                time.sleep(0.1)  # Sleep for a short interval to avoid busy-waiting
            else:
                self.logger.debug(f"Closing valve after {duration} seconds as planned")
            return int(elapsed_time)

        finally:
            self.control(RelayValveState.CLOSED)
            if (elapsed_time + TOLERANCE) < duration and not stop_event.is_set():
                # If the valve was closed early without a stop event, log an error
                raise Exception(
                    f"Valve {self.pin} was closed early after {int(elapsed_time)} seconds, expected {duration} seconds."
                )