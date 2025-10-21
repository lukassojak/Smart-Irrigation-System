from enum import Enum

class ControllerState(Enum):
    IDLE = "idle"
    IRRIGATING = "irrigating"
    STOPPING = "stopping"                     # Stopping irrigation
    ERROR = "error"


class IrrigationState(Enum):
    IDLE = "idle"                           # No irrigation is currently happening, circuit is ready
    WAITING_FOR_FLOW = "waiting_for_flow"   # Waiting for the main valve flow capacity to be available
    IRRIGATING = "irrigating"               # Currently irrigating
    FINISHED = "finished"                   # Irrigation has finished
    ERROR = "error"                         # An error occurred
    STOPPED = "stopped"                     # Irrigation has been stopped by the user
    INTERRUPTED = "interrupted"              # Irrigation was interrupted (e.g., power loss)
    DISABLED = "disabled"                   # Irrigation circuit is disabled


class IrrigationOutcome(Enum):
    """High-level result state of an irrigation attempt."""
    SUCCESS = "success"          # Irrigation completed successfully
    FAILED = "failed"            # Irrigation failed due to an error
    STOPPED = "stopped"          # Irrigation was manually stopped by the user
    INTERRUPTED = "interrupted"   # Irrigation was interrupted (e.g., power loss)
    SKIPPED = "skipped"          # Irrigation was skipped (e.g., due to conditions)


class RelayValveState(Enum):
    OPEN = "open"                           # Relay valve is open
    CLOSED = "closed"                       # Relay valve is closed


class Environment(Enum):
    PC = "pc"                               # Running on a PC, e.g., for testing
    RASPBERRY_PI_PICO_W = "raspberry_pi_pico_w"  # Running on a Raspberry Pi Pico W
    RASPBERRY_PI_ZERO_W = "raspberry_pi_zero_w"  # Running on a Raspberry Pi Zero W


# Deprecated, not used anymore
class SoilMoisture(Enum):
    TOO_WET = 0
    TOO_DRY = 1
    OPTIMAL = 2


# Deprecated, not used anymore
class MoistureSensorState(Enum):
    WET = 3
    DRY = 4

SECONDS_IN_MUNUTE = 60
TEMP_WATERING_TIME = 10