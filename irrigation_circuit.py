from relay_valve import RelayValve
from deprecated.soil_moisture_sensor import SoilMoistureSensorPair
from enums import TEMP_WATERING_TIME
from drippers import Drippers


class IrrigationCircuit:
    def __init__(self, name, circuit_number, relay_pin, enabled, standard_flow_seconds, interval_days, drippers, sensor_pins=[]):
        self.number = circuit_number
        self.name = name
        self.valve = RelayValve(relay_pin)
        self.enabled = enabled
        self.standard_flow_seconds = standard_flow_seconds      # Base watering time in seconds
        self.interval_days = interval_days
        self.sensors = [SoilMoistureSensorPair(pin1, pin2) for pin1, pin2 in sensor_pins]

        self.drippers = Drippers()                              # Instance of Drippers to manage dripper flow rates 

    
    def get_circuit_consumption(self):
        """Returns the total consumption of all drippers in liters per hour."""
        return self.drippers.get_consumption()


    def irrigate_automatic(self, stop_event):
        """Starts the automatic irrigation process depending on global conditions"""

        print(f"I-Circuit  {self.number}: Starting irrigation")


        self.valve.open(10, stop_event)


    def irrigate(self, duration, stop_event):
        """Starts the irrigation process for a specified duration"""

        print(f"I-Circuit  {self.number}: Starting irrigation")


        self.valve.open(duration, stop_event)
        