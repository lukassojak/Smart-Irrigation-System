from relay_valve import RelayValve
from deprecated.soil_moisture_sensor import SoilMoistureSensorPair
from enums import TEMP_WATERING_TIME
from drippers import Drippers
from correction_factors import CorrectionFactors


class IrrigationCircuit:
    def __init__(self, name: str, circuit_id: int, relay_pin: int,
                 enabled: bool, even_area_mode: bool, target_mm: float,
                 zone_area_m2: float, liters_per_minimum_dripper: float,
                 interval_days: int, drippers: Drippers,
                 correction_factors: CorrectionFactors, sensor_pins=None):
        self.id = circuit_id
        self.name = name
        self.valve = RelayValve(relay_pin)
        self.enabled = enabled
        self.even_area_mode = even_area_mode                            # True if the circuit uses even area mode
        self.target_mm = target_mm                                      # Base target watering depth in mm (for even area mode, otherwise None)
        self.zone_area_m2 = zone_area_m2                                # Area of the zone in square meters (for even area mode, otherwise None)
        self.liters_per_minimum_dripper = liters_per_minimum_dripper    # Base watering volume in liters per minimum dripper (for non-even area mode, otherwise None)
        # Ask Drippers for the dripper with the minimum flow rate in liters per hour in configuration

        self.interval_days = interval_days
        self.sensors = [SoilMoistureSensorPair(pin1, pin2) for pin1, pin2 in sensor_pins] if sensor_pins else []

        self.drippers = drippers                                        # Instance of Drippers to manage dripper flow rates
        self.correction_factors = correction_factors                    # Instance of CorrectionFactors for local adjustments

    
    def get_circuit_consumption(self):
        """Returns the total consumption of all drippers in liters per hour."""
        return self.drippers.get_consumption()


    def irrigate_automatic(self, stop_event):
        """Starts the automatic irrigation process depending on global conditions"""

        print(f"I-Circuit  {self.id}: Starting irrigation")


        self.valve.open(10, stop_event)


    def irrigate(self, duration, stop_event):
        """Starts the irrigation process for a specified duration"""

        print(f"I-Circuit  {self.id}: Starting irrigation")


        self.valve.open(duration, stop_event)
        