import time

class RelayValve:
    def __init__(self, pin):
        self.pin = pin

    def control(self, action_open):
        """Enables or disables the relay valve to start or stop watering"""

        if action_open:
            print(f"Valve      {self.pin}: OPEN-VALVE ")    # replace with GPIO.output(self.pin, GPIO.HIGH) in actual implementation
        else:
            print(f"Valve      {self.pin}: CLOSE-VALVE ")   # replace with GPIO.output(self.pin, GPIO.LOW) in actual implementation
    
    def open(self, duration, stop_event):
        """Opens the valve for a specified duration"""

        print(f"Valve      {self.pin}: valve will be opened for {duration} seconds")
        self.control(True)


        # try-except block provides a fail-safe mechanism to ensure the valve is not left open indefinitely
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                if stop_event.is_set():
                    print(f"Valve      {self.pin}: Closing valve early.")
                    break
                time.sleep(0.1)  # Sleep for a short interval to avoid busy-waiting
            else:
                print(f"Valve      {self.pin}: Closing valve duly after {duration} seconds")
        finally:
            self.control(False)
            elapsed_time = time.time() - start_time
            print(f"Valve      {self.pin}: valve was open for {elapsed_time:.0f} seconds")
            if elapsed_time < duration:
                # to indicate that the valve was closed early, throw an exception
                raise Exception(f"Valve {self.pin} was closed early after {elapsed_time:.0f} seconds, expected {duration} seconds.")