

class IrrigationCircuit:
    def __init__(self, name, circuit_number, relay_pin, sensor_pins=[]):
        self.number = circuit_number
        self.name = name
        self.valve = RelayValve(relay_pin)
        self.sensors = [SoilMoistureSensorPair(pin1, pin2) for pin1, pin2 in sensor_pins]
        self.too_dry_irrigation_time = 15

    def read_moisture(self):
        """
        Reads the moisture sensors and returns list of readings

        Returns:
            list: A list of moisture sensor readings. If no sensors are present, returns an empty list.
        """

        if not self.sensors:
            return []

        return [sensor.read() for sensor in self.sensors]
    
    def irrigate_automatic(self, stop_event):
        """Starts the automatic irrigation process depending on global conditions"""

        print(f"Starting irrigation for circuit number {self.number}: {self.name}")


        self.valve.open(10, stop_event)

    def irrigate_too_dry(self, stop_event):
        """Starts the irrigation process set for too dry soil"""

        print(f"Starting irrigation for too dry soil for circuit number {self.number}: {self.name}")

        self.valve.open(self.too_dry_irrigation_time, stop_event)

    # change the duration to water volume
    def irrigate(self, duration, stop_event):
        """Starts the irrigation process for a specified duration"""

        print(f"Starting irrigation for circuit number {self.number}: {self.name}")

        # TODO: Implement the automatic time calculation based on global conditions

        self.valve.open(duration, stop_event)
        