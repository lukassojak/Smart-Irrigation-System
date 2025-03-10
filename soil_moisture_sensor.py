import random
from enums import MoistureSensorState, SoilMoisture

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