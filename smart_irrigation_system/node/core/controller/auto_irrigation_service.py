# smart_irrigation_system/node/core/controller/auto_irrigation_service.py

from collections.abc import Callable
from datetime import datetime

import smart_irrigation_system.node.utils.time_utils as time_utils

from smart_irrigation_system.node.config.global_config import GlobalConfig

from smart_irrigation_system.node.utils.logger import get_logger


ALLOWED_TIME_DRIFT_SECONDS = 90 # Make configurable if needed


class AutoIrrigationService:
    """
    Service responsible only for deciding *whether* automatic irrigation
    should start based on scheduled time.

    It emits a callback when the scheduled moment (with small drift window)
    is reached. It guarantees at most one trigger per day.
    """

    def __init__(self, global_config: GlobalConfig,
                 on_auto_irrigation_demand: Callable[[], None]) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self._on_auto_irrigation_demand = on_auto_irrigation_demand
        self.global_config: GlobalConfig = global_config
        self._runtime_enabled: bool = True if self.global_config.automation.enabled else False

        # Last time automatic irrigation was triggered
        self._last_trigger: datetime | None = None       # In future, should be persisted (CircuitStateManager)

    
    # ===========================================================================================================
    # Public API
    # ===========================================================================================================
    
    @property
    def is_runtime_enabled(self) -> bool:
        """Returns whether auto-irrigation is enabled at runtime."""
        return self._runtime_enabled

    def tick(self) -> None:
        """
        Periodic evaluation of auto-irrigation conditions (scheduled time).

        Should be called periodically by scheduler. If the current time matches
        a configured irrigation time, it triggers an irrigation request.
        """

        if not self.global_config.automation.enabled or not self._runtime_enabled:
            return

        if self._is_time_to_irrigate():
            # Trigger irrigation demand to the controller
            self.logger.debug("Auto-irrigation time reached, triggering irrigation demand.")
            self._on_auto_irrigation_demand()
            self._last_trigger = time_utils.now()


    def enable_runtime(self) -> None:
        """Enable auto-irrigation at runtime."""

        if not self.global_config.automation.enabled:
            self.logger.warning("Attempted to enable auto-irrigation at runtime, but it is disabled in global configuration.")
            return
        
        if self._runtime_enabled:
            self.logger.debug("Auto-irrigation is already enabled at runtime.")
            return

        self._runtime_enabled = True

    def disable_runtime(self) -> None:
        """Disable auto-irrigation at runtime."""

        if not self._runtime_enabled:
            self.logger.debug("Auto-irrigation is already disabled at runtime.")
            return

        self._runtime_enabled = False
    
    # ===========================================================================================================
    # Private Methods
    # ===========================================================================================================
    
    def _is_time_to_irrigate(self) -> bool:
        # Compute today's scheduled datetime
        now: datetime = time_utils.now()
        target = now.replace(
            hour=self.global_config.automation.scheduled_hour,
            minute=self.global_config.automation.scheduled_minute,
            second=0,
            microsecond=0
        )

        # Already triggered today
        if self._last_trigger and time_utils.is_same_day(self._last_trigger, now):
            return False
        
        # Check if current time is within allowed drift
        time_diff = abs((now - target).total_seconds())
        return time_diff <= ALLOWED_TIME_DRIFT_SECONDS
        

