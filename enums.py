from enum import Enum


class SoilMoisture(Enum):
    TOO_WET = 0
    TOO_DRY = 1
    OPTIMAL = 2

class MoistureSensorState(Enum):
    WET = 3
    DRY = 4


SECONDS_IN_MUNUTE = 60
TEMP_WATERING_TIME = 10