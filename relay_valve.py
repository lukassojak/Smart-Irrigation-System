import time


class RelayValve:
    def __init__(self, pin):
        self.pin = pin

    def control(self, action_open):
        """Enables or disables the relay valve to start or stop watering"""

        if action_open:
            print(f"Opening valve {self.pin} (watering)")
        else:
            print(f"Closing valve {self.pin} (stopping watering)")
    
    def open(self, duration, stop_event):
        """Opens the valve for a specified duration"""

        print(f"Opening valve {self.pin} for {duration} seconds")
        self.control(True)

        for _ in range(duration):
            if stop_event.is_set():
                print(f"Interrupted! Closing valve {self.pin} early.")
                break
            time.sleep(1)

        self.control(False)

        