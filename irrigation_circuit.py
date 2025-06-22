from relay_valve import RelayValve
from deprecated.soil_moisture_sensor import SoilMoistureSensorPair
from enums import TEMP_WATERING_TIME
from dripper import Dripper


class IrrigationCircuit:
    def __init__(self, name, circuit_number, relay_pin, sensor_pins=[]):
        self.number = circuit_number
        self.name = name
        self.valve = RelayValve(relay_pin)
        self.sensors = [SoilMoistureSensorPair(pin1, pin2) for pin1, pin2 in sensor_pins]

        self.drippers = []                      # List of drippers in the circuit
        self.consumption = 0                    # in liters per hour
        self.base_irrigation_volume = 0         # in liters

    
    def add_dripper(self, liters_per_hour) -> int:
        """Adds a dripper to the circuit"""

        self.consumption += liters_per_hour
        self.base_irrigation_volume += liters_per_hour
        dripper_number = len(self.drippers)
        dripper = Dripper(dripper_number, liters_per_hour)
        self.drippers.append(dripper)
        return dripper_number
    
    def remove_dripper_by_number(self, dripper_number) -> bool:
        """Removes a dripper from the circuit by it's number"""

        if dripper_number < len(self.drippers):
            dripper = self.drippers[dripper_number]
            self.consumption -= dripper.liters_per_hour
            self.base_irrigation_volume -= dripper.liters_per_hour
            del self.drippers[dripper_number]
            return True
        else:
            return False
    
    def remove_dripper_by_object(self, dripper) -> bool:
        """Removes a dripper from the circuit by object"""

        if dripper in self.drippers:
            self.consumption -= dripper.liters_per_hour
            self.base_irrigation_volume -= dripper.liters_per_hour
            self.drippers.remove(dripper)
            return True
        else:
            return False
        
    def remove_dripper_by_consumption(self, liters_per_hour) -> bool:
        """Removes a dripper from the circuit by consumption"""

        for dripper in self.drippers:
            if dripper.liters_per_hour == liters_per_hour:
                self.consumption -= dripper.liters_per_hour
                self.base_irrigation_volume -= dripper.liters_per_hour
                self.drippers.remove(dripper)
                return True
        return False
    
    def irrigate_automatic(self, stop_event):
        """Starts the automatic irrigation process depending on global conditions"""

        print(f"I-Circuit  {self.number}: Starting irrigation")


        self.valve.open(10, stop_event)


    def irrigate(self, duration, stop_event):
        """Starts the irrigation process for a specified duration"""

        print(f"I-Circuit  {self.number}: Starting irrigation")


        self.valve.open(duration, stop_event)
        