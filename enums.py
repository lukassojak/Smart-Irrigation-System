from enum import Enum


class SoilMoisture(Enum):
    TOO_WET = 0
    TOO_DRY = 1
    OPTIMAL = 2

class MoistureSensorState(Enum):
    WET = 3
    DRY = 4