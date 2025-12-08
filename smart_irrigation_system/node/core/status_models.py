"""
Data models representing the runtime and persistent state of irrigation circuits.

These dataclasses provide a separation between:
- realtime runtime state from `IrrigationCircuit`
- persistent snapshot state from `CircuitStateManager`
- unified combined state served to UI / API via `IrrigationController`
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from smart_irrigation_system.node.core.enums import IrrigationState, IrrigationOutcome, SnapshotCircuitState, ControllerState


# ========================================
# Circuit Runtime (IrrigationCircuit)
# ========================================

@dataclass
class CircuitRuntimeStatus:
    """Class to represent the runtime status of an irrigation circuit. DTO from IrrigationCircuit."""
    state: IrrigationState
    is_irrigating: bool
    current_duration: Optional[int]
    target_duration: Optional[int]
    current_volume: Optional[float]
    target_volume: Optional[float]
    progress_percentage: Optional[float]
    timestamp: datetime


# ========================================
# Circuit Persistent Snapshot (CircuitStateManager)
# ========================================

@dataclass
class CircuitSnapshot:
    """Class to represent the persistent snapshot state of an irrigation circuit."""
    id: int
    circuit_state: SnapshotCircuitState
    last_decision: Optional[datetime]
    last_outcome: Optional[IrrigationOutcome]
    last_irrigation: Optional[datetime]
    last_duration: Optional[int]
    last_volume: Optional[float]
    timestamp: Optional[datetime]


# ========================================
# Circuit Combined Status (IrrigationController)
# ========================================

@dataclass
class CircuitStatus:
    """Class to represent the combined status of an irrigation circuit."""
    id: int
    name: str
    runtime_status: CircuitRuntimeStatus
    snapshot: CircuitSnapshot


# ========================================
# Controller Status Summary
# ========================================

@dataclass
class ControllerStatusSummary:
    """Class to represent a summary of the controller's overall status."""
    circuit_ids: list[int]
    controller_state: ControllerState


# ========================================
# Controller Full Status
# ========================================

@dataclass
class ControllerFullStatus:
    """Class to represent the full status of the controller, including all circuits."""
    summary: ControllerStatusSummary
    circuit_statuses: dict[int, CircuitStatus]