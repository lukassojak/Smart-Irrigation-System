# smart_irrigation_system/node/interfaces.py

import threading

from datetime import datetime
from typing import Protocol

from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.irrigation_result import IrrigationResult

from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions


# ==================================================================================================================
# CIRCUIT LEVEL INTERFACES
# ==================================================================================================================

class CircuitPlanningLike(Protocol):
    """
    Interface for planner's view of an irrigation circuit.
    """

    id: int
    name: str

    def needs_irrigation(self, state_manager: CircuitStateManager) -> bool:
        """Determine if the circuit needs irrigation based on its state and conditions."""

        ...

    @property
    def circuit_consumption(self) -> float:
        ...


class CircuitExecutionLike(Protocol):
    """
    Interface for executor's view of an irrigation circuit.
    """

    id: int
    
    def irrigate_auto(self,
                      global_config: GlobalConfig,
                      global_conditions: GlobalConditions,
                      stop_event: threading.Event) -> IrrigationResult:
        ...

    def irrigate_man(self,
                     target_volume: float,
                     stop_event: threading.Event) -> IrrigationResult:
        ...
        
    def flow_overload_timeout_triggered(self, start_time: datetime) -> IrrigationResult:
        ...

    def is_safe_to_irrigate(self) -> bool:
        """Run-time safety check before starting irrigation. Shouldn't be called from planning phase."""

        ...


# ==================================================================================================================
# BATCH STRATEGY INTERFACE
# ==================================================================================================================

class BatchStrategyLike(Protocol):
    """
    Interface for pluggable batching strategies.
    """

    def select_batches(self, circuits: list[CircuitPlanningLike]) -> list[list[int]]:
        ...

