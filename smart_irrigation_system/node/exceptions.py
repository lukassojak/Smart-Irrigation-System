# smart_irrigation_system/node/exceptions.py

from smart_irrigation_system.node.core.enums import RelayValveState


class RelayValveError(Exception):
    """Custom exception for RelayValve errors."""
    pass

class RelayValveStateError(RelayValveError):
    """
    Exception raised when the relay valve fails to reach the desired state.
    Attributes:
        attempted_state (RelayValveState): The state that was attempted to be set.
    """
    def __init__(self, message: str, attempted_state: RelayValveState):
        super().__init__(message)
        self.attempted_state = attempted_state

class GPIOInitializationError(RelayValveError):
    """Exception raised when GPIO initialization fails."""
    pass

class GPIOWriteError(RelayValveError):
    """Exception raised when writing to GPIO fails."""
    pass