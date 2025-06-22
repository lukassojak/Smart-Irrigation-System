

class RelayValve:
    def __init__(self, pin):
        self.pin = pin

    def control(self, action_open):
        """Enables or disables the relay valve to start or stop watering"""

        if action_open:
            print(f"Valve      {self.pin}: OPEN-VALVE ")
        else:
            print(f"Valve      {self.pin}: CLOSE-VALVE ")
    
    def open(self, duration, stop_event):
        """Opens the valve for a specified duration"""

        print(f"Valve      {self.pin}: valve will be opened for {duration} seconds")
        self.control(True)

        if not stop_event.wait(duration):
            print(f"Valve      {self.pin}: Closing valve duly after {duration} seconds")
        else:
            print(f"Valve      {self.pin}: Closing valve early.")

        self.control(False)
        