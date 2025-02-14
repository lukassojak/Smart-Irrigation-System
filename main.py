import random
from enum import Enum
import time

# This is the main file that will be run on the Raspberry Pi Pico


class SoilMoisture(Enum):
    TOO_WET = 0
    TOO_DRY = 1
    OPTIMAL = 2

class MoistureSensorState(Enum):
    WET = 3
    DRY = 4


class GlobalConditions:
    """Gets the global conditions from the local weather station"""
    # For now, it will just use random values

    def __init__(self):
        self.temperature = 0
        self.rainfall = 0
        self.sunlight = 0

    def update(self):
        """Simulates new global conditions"""

        self.temperature = random.uniform(10, 35)   # °C in average in the last X hours
        self.rainfall = random.uniform(0, 10)       # mm in the last X hours
        self.sunlight = random.uniform(0, 100)      # % average in the last X hours

    def get_conditions(self):
        """Returns the current global conditions as a dictionary"""

        return {
            "temperature": self.temperature,
            "rainfall": self.rainfall,
            "sunlight": self.sunlight
        }


class IrrigationCircuit:
    def __init__(self, name, circuit_number, relay_pin, sensor_pins=[]):
        self.number = circuit_number
        self.name = name
        self.valve = RelayValve(relay_pin)
        self.sensors = [SoilMoistureSensorPair(pin1, pin2) for pin1, pin2 in sensor_pins]
        self.too_dry_irrigation_time = 5

    def read_moisture(self):
        """
        Reads the moisture sensors and returns list of readings

        Returns:
            list: A list of moisture sensor readings. If no sensors are present, returns an empty list.
        """

        if not self.sensors:
            return []

        return [sensor.read() for sensor in self.sensors]
    
    def irrigate_automatic(self):
        """Starts the automatic irrigation process depending on global conditions"""

        print(f"Starting irrigation for circuit number {self.number} named {self.name}")

        # TODO: Implement the automatic time calculation based on global conditions
        # For now, it will just open the valve for 5 seconds

        self.valve.open(5)

    def irrigate_too_dry(self):
        """Starts the irrigation process set for too dry soil"""

        print(f"Starting irrigation for too dry soil for circuit number {self.number} named {self.name}")

        self.valve.open(self.too_dry_irrigation_time)


class SoilMoistureSensorPair:
    """Represents a pair of soil moisture sensors"""
    def __init__(self, pin1, pin2):
        self.pin1 = pin1
        self.pin2 = pin2

    def read(self):
        """Reads the soil moisture sensor values and returns the combined reading"""

        # For now, it will just return a random value
        pin1_reading = random.choice([MoistureSensorState.WET, MoistureSensorState.DRY])
        pin2_reading = random.choice([MoistureSensorState.WET, MoistureSensorState.DRY])

        if (pin1_reading == MoistureSensorState.WET and pin2_reading == MoistureSensorState.WET):
            reading = SoilMoisture.TOO_WET
        elif (pin1_reading == MoistureSensorState.DRY and pin2_reading == MoistureSensorState.DRY):
            reading = SoilMoisture.TOO_DRY
        else:
            reading = SoilMoisture.OPTIMAL

        return reading


class RelayValve:
    def __init__(self, pin):
        self.pin = pin

    def control(self, action_open):
        """Enables or disables the relay valve to start or stop watering"""

        if action_open:
            print(f"Opening valve {self.pin} (watering)")
        else:
            print(f"Closing valve {self.pin} (stopping watering)")
    
    def open(self, duration):
        """Opens the valve for a specified duration"""

        print(f"Opening valve {self.pin} for {duration} seconds")
        self.control(True)
        time.sleep(duration)
        self.control(False)


class IrrigationController:
    """The main irrigation controller that manages all the irrigation circuits"""

    def __init__(self):
        self.global_conditions = GlobalConditions()
        self.circuits = {}
        self.circuits_count = 0

    def add_circuit(self, name, relay_pin, sensor_pins=[]):
        """Adds a new irrigation circuit to the controller"""

        circuit_number = self.circuits_count
        circuit = IrrigationCircuit(name, circuit_number, relay_pin, sensor_pins)
        self.circuits[circuit_number] = circuit
        self.circuits_count += 1

    
    def print_conditions(self):
        self.global_conditions.update()
        conditions = self.global_conditions.get_conditions()

        print("Current global conditions:")
        print(conditions)
    
    def get_conditions(self):
        return self.global_conditions.get_conditions()
    
    def perform_irrigation(self):
        """Performs irrigation for all circuits based on the current conditions"""

        global_conditions = self.get_conditions()

        for circuit in self.circuits.values():
            moisture_readings = circuit.read_moisture()

            if SoilMoisture.TOO_WET in moisture_readings:
                print(f"Soil too wet in the circuit number {circuit.number} named {circuit.name}, \
                      skipping irrigation cycle for the circuit ...")
                continue

            if SoilMoisture.TOO_DRY in moisture_readings:
                print(f"Soil too dry in the circuit number {circuit.number} named {circuit.name}, \
                      performing irrigation cycle for dry conditions ...")
                circuit.irrigate_too_dry()
                continue

            if moisture_readings == []:
                print(f"No soil moisture sensors in the circuit number {circuit.number} named {circuit.name}, \
                      irrigation cycle depends only on global conditions ...")

            # optimal soil moisture here, irrigate according to global conditions
            circuit.irrigate_automatic()