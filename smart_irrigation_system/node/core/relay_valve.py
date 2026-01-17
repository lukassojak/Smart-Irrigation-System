try:
    import RPi.GPIO as GPIO
    GPIO_SUPPORTED = True
# if ImportError or RuntimeError occurs, use a dummy GPIO class for testing
except (ImportError, RuntimeError):
    GPIO_SUPPORTED = False
    class GPIO:
        BCM = None
        IN = None
        OUT = None
        PUD_UP = None
        LOW = None
        HIGH = None
        FALLING = None
        RISING = None
        BOTH = None
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode, pull_up_down=None): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def input(pin): return False
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None): pass
        @staticmethod
        def cleanup(pins=None): pass
    
    GPIO = GPIO  # Use the dummy GPIO class for testing

import time
import threading
from typing import Optional, Callable

from smart_irrigation_system.node.utils.logger import get_logger
from smart_irrigation_system.node.core.enums import RelayValveState
from smart_irrigation_system.node.exceptions import (
    RelayValveStateError,
    GPIOInitializationError,
    GPIOWriteError,
)

MAX_RETRIES = 3  # Maximum number of retries for state change
RETRY_DELAY = 1  # Delay between retries, in seconds
TOLERANCE = 0.5  # Tolerance for time checks, in seconds


class RelayValve:
    _gpio_initialized = False

    def __init__(self, pin: int):
        # Initialize the relay valve logger with a specific pin number
        self.logger = get_logger(f"RelayValve-{pin}")
        self.pin = pin
        
        self._init_gpio()
        self._state = RelayValveState.CLOSED  # Default state is CLOSED
        self._lock = threading.Lock()

        self.logger.info(f"RelayValve initialized on pin {self.pin}")
    
    def _init_gpio(self) -> None:
        try:
            if not RelayValve._gpio_initialized:
                GPIO.setmode(GPIO.BCM)
                RelayValve._gpio_initialized = True
            GPIO.setup(self.pin, GPIO.OUT)  # Set the pin as an output
            GPIO.output(self.pin, GPIO.HIGH)  # Ensure the valve is closed initially
        except Exception as e:
            raise GPIOInitializationError(f"Failed to initialize GPIO for pin {self.pin}: {e}")


    # ============================================================================================================
    # Public API
    # ============================================================================================================

    @property
    def state(self) -> RelayValveState:
        """Returns the current state of the relay valve"""
        return self._state

    def set_state(self, new_state: RelayValveState, retry: int = MAX_RETRIES) -> None:
        """
        High-level safe request to change the valve state with retries.
        
        :raises RelayValveStateError: If the valve fails to reach the desired state after retries.
        """
        if new_state == self._state:
            self.logger.warning(f"Valve is already in state {new_state}. No action taken.")
            return
        
        last_exception: Optional[Exception] = None
        for attempt in range(retry):
            try:
                with self._lock:
                    self._apply_state(new_state)
                return  # Successfully changed state
            except GPIOWriteError as e:
                last_exception = e
                self.logger.error(f"Attempt {attempt + 1} to set valve state failed: {e}")
                time.sleep(RETRY_DELAY)
        
        raise RelayValveStateError("Failed to set valve state", attempted_state=new_state) from last_exception


    
    # ============================================================================================================
    # Private Methods
    # ============================================================================================================

    def _apply_state(self, new_state: RelayValveState) -> None:
        """
        Low-level method to change the valve state without retries.
        """
        expected_gpio = GPIO.LOW if new_state == RelayValveState.OPEN else GPIO.HIGH
        GPIO.output(self.pin, expected_gpio)

        # TODO: Add verification logic if hardware feedback is available

        self._state = new_state
        self.logger.debug(f"Valve on pin {self.pin} -> {new_state.name}")