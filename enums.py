from enum import Enum


class IrrigationState(Enum):
    IDLE = "idle"                           # No irrigation is currently happening
    WAITING_FOR_FLOW = "waiting_for_flow"   # Waiting for the main valve flow capacity to be available
    IRRIGATING = "irrigating"               # Currently irrigating
    FINISHED = "finished"                   # Irrigation has finished
    ERROR = "error"                         # An error occurred
    STOPPED = "stopped"                     # Irrigation has been stopped by the user

class SoilMoisture(Enum):
    TOO_WET = 0
    TOO_DRY = 1
    OPTIMAL = 2

class MoistureSensorState(Enum):
    WET = 3
    DRY = 4

SECONDS_IN_MUNUTE = 60
TEMP_WATERING_TIME = 10