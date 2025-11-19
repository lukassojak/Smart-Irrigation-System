from datetime import datetime
from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.enums import IrrigationOutcome


def create_flow_overload(circuit_id: int, start_time: datetime, target_duration: int, target_water_amount: float) -> IrrigationResult:
    """Factory function to create a flow overload irrigation result."""
    return IrrigationResult(
        circuit_id=circuit_id,
        success=False,
        outcome=IrrigationOutcome.SKIPPED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Timeout: Flow overload."
    )


def create_skipped_due_to_conditions(circuit_id: int, start_time: datetime, target_duration: int, target_water_amount: float) -> IrrigationResult:
    """Factory function to create a skipped due to conditions irrigation result."""
    return IrrigationResult(
        circuit_id=circuit_id,
        success=True,
        outcome=IrrigationOutcome.SKIPPED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Skipped due to environmental conditions (negative adjustment)"
    )

def create_failure_invalid_water_amount(circuit_id: int, start_time: datetime, target_duration: int, target_water_amount: float) -> IrrigationResult:
    """Factory function to create a failure due to invalid water amount irrigation result."""
    return IrrigationResult(
        circuit_id=circuit_id,
        success=False,
        outcome=IrrigationOutcome.FAILED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Invalid target water amount. Must be greater than zero."
    )

def create_failure_circuit_not_idle(circuit_id: int, start_time: datetime, target_duration: int, target_water_amount: float) -> IrrigationResult:
    """Factory function to create a failure due to circuit not being idle irrigation result."""
    return IrrigationResult(
        circuit_id=circuit_id,
        success=False,
        outcome=IrrigationOutcome.FAILED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Circuit is not in IDLE state"
    )

def create_interrupted(circuit_id: int, start_time: datetime, elapsed, actual_water_amout: float, target_duration: int, target_water_amount: float, reason: str) -> IrrigationResult:
    """Factory function to create an interrupted irrigation result."""
    return IrrigationResult(
        circuit_id=circuit_id,
        success=False,
        outcome=IrrigationOutcome.INTERRUPTED,
        start_time=start_time,
        completed_duration=elapsed,
        target_duration=target_duration,
        actual_water_amount=actual_water_amout,
        target_water_amount=target_water_amount,
        error=f"Irrigation interrupted: {reason}"
    )

def create_general(circuit_id: int, start_time: datetime, completed_duration: int, target_duration: int, actual_water_amount: float, target_water_amount: float, success: bool, outcome: IrrigationOutcome, error: str = None) -> IrrigationResult:
    """Factory function to create a general irrigation result."""
    return IrrigationResult(
        circuit_id=circuit_id,
        success=success,
        outcome=outcome,
        start_time=start_time,
        completed_duration=completed_duration,
        target_duration=target_duration,
        actual_water_amount=actual_water_amount,
        target_water_amount=target_water_amount,
        error=error
    )