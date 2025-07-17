import time
from smart_irrigation_system.logger import get_logger

class RelayValve:
    def __init__(self, pin):
        # Initialize the relay valve logger with a specific pin number
        self.logger = get_logger(f"RelayValve_{pin}")
        self.pin = pin
        self.logger.info(f"RelayValve initialized on pin {self.pin}")

    def control(self, action_open):
        """Enables or disables the relay valve to start or stop watering"""

        if action_open:
            print(f"Valve      {self.pin}: OPEN-VALVE ")    # replace with GPIO.output(self.pin, GPIO.HIGH) in actual implementation
        else:
            print(f"Valve      {self.pin}: CLOSE-VALVE ")   # replace with GPIO.output(self.pin, GPIO.LOW) in actual implementation
    
    def open(self, duration, stop_event):
        """Opens the valve for a specified duration"""

        self.logger.info(f"Valve will be opened for {duration} seconds.")
        self.control(True)
    
        # try-except block provides a fail-safe mechanism to ensure the valve is not left open indefinitely
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                if stop_event.is_set():
                    self.logger.info(f"Closing valve early due to stop event after {time.time() - start_time:.0f} seconds")
                    break
                time.sleep(0.1)  # Sleep for a short interval to avoid busy-waiting
            else:
                self.logger.info(f"Closing valve after {duration} seconds as planned")
        finally:
            self.control(False)
            elapsed_time = time.time() - start_time
            if elapsed_time < duration and not stop_event.is_set():
                # If the valve was closed early without a stop event, log an error
                self.logger.error(f"Valve {self.pin} was closed early after {elapsed_time:.0f} seconds, expected {duration} seconds.")
                raise Exception(f"Valve {self.pin} was closed early after {elapsed_time:.0f} seconds, expected {duration} seconds.")