from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from smart_irrigation_system.enums import IrrigationOutcome


@dataclass
class IrrigationResult:
    """Class to encapsulate the result of an irrigation attempt."""
    circuit_id: int
    success: bool
    outcome: IrrigationOutcome
    start_time: datetime
    completed_duration: int
    target_duration: int
    actual_water_amount: float
    target_water_amount: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the result into a JSON-serializable dict."""
        return {
            "circuit_id": self.circuit_id,
            "success": self.success,
            "outcome": self.outcome.value,
            "start_time": self.start_time.isoformat(),
            "completed_duration": self.completed_duration,
            "target_duration": self.target_duration,
            "actual_water_amount": self.actual_water_amount,
            "target_water_amount": self.target_water_amount,
            "error": self.error
        }

    @staticmethod
    def from_dict(data: dict) -> "IrrigationResult":
        """Reconstruct an IrrigationResult from a dict (e.g. loaded from JSON)."""
        return IrrigationResult(
            circuit_id=data["circuit_id"],
            success=data["success"],
            outcome=IrrigationOutcome(data["outcome"]),
            start_time=datetime.fromisoformat(data["start_time"]),
            completed_duration=data["completed_duration"],
            target_duration=data["target_duration"],
            actual_water_amount=data["actual_water_amount"],
            target_water_amount=data["target_water_amount"],
            error=data.get("error")
        )

