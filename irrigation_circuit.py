from relay_valve import RelayValve
from deprecated.soil_moisture_sensor import SoilMoistureSensorPair
from enums import TEMP_WATERING_TIME
from drippers import Drippers
from correction_factors import CorrectionFactors


class IrrigationCircuit:
    def __init__(self, name: str, circuit_number: int, relay_pin: int, enabled: bool, standard_flow_seconds: int, interval_days: int, drippers: Drippers, correction_factors: CorrectionFactors, sensor_pins=None):
        self.id = circuit_number
        self.name = name
        self.valve = RelayValve(relay_pin)
        self.enabled = enabled
        self.standard_flow_seconds = standard_flow_seconds      # Base watering time in seconds
        self.interval_days = interval_days
        self.sensors = [SoilMoistureSensorPair(pin1, pin2) for pin1, pin2 in sensor_pins] if sensor_pins else []

        self.drippers = drippers                                # Instance of Drippers to manage dripper flow rates
        self.correction_factors = correction_factors            # Instance of CorrectionFactors for local adjustments 

    
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
        