from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from smart_irrigation_system.node.core.enums import IrrigationOutcome


@dataclass
class IrrigationResult:
    """Class to encapsulate the result of an irrigation attempt."""
    circuit_id: int
    success: bool   # Outcomes SUCCESS, SKIPPED, and STOPPED are considered successful
    outcome: IrrigationOutcome
    target_duration: int
    target_water_amount: float
    was_manual_run: Optional[bool] = None # None for unknown (interrupted)
    start_time: Optional[datetime] = None
    completed_duration: Optional[int] = None  # None for interrupted
    actual_water_amount: Optional[float] = None  # None for interrupted
    error: Optional[str] = None
    # Extended fields for telemetry, weather-model context and carry-over
    base_water_amount: Optional[float] = None
    standard_conditions_solar: Optional[float] = None
    standard_conditions_rain: Optional[float] = None
    standard_conditions_temp: Optional[float] = None
    actual_solar: Optional[float] = None
    actual_rain: Optional[float] = None
    actual_temp: Optional[float] = None
    carry_over_applied: bool = False
    even_area_mode: Optional[bool] = None
    dynamic_interval_enabled: Optional[bool] = None
    irrigation_volume_threshold_percent: Optional[int] = None
    # target_mm, and actual_mm are set on the server

    def to_dict(self) -> dict:
        """Convert the result into a JSON-serializable dict."""
        return {
            "was_manual_run": self.was_manual_run,
            "circuit_id": self.circuit_id,
            "success": self.success,
            "outcome": self.outcome.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "completed_duration": self.completed_duration,
            "target_duration": self.target_duration,
            "actual_water_amount": self.actual_water_amount,
            "target_water_amount": self.target_water_amount,
            "error": self.error
        ,
            "base_water_amount": self.base_water_amount,
            "standard_conditions_solar": self.standard_conditions_solar,
            "standard_conditions_rain": self.standard_conditions_rain,
            "standard_conditions_temp": self.standard_conditions_temp,
            "actual_solar": self.actual_solar,
            "actual_rain": self.actual_rain,
            "actual_temp": self.actual_temp,
            "carry_over_applied": self.carry_over_applied,
            "even_area_mode": self.even_area_mode,
            "dynamic_interval_enabled": self.dynamic_interval_enabled,
            "irrigation_volume_threshold_percent": self.irrigation_volume_threshold_percent,
        }

    @staticmethod
    def from_dict(data: dict) -> "IrrigationResult":
        """Reconstruct an IrrigationResult from a dict (e.g. loaded from JSON)."""
        return IrrigationResult(
            was_manual_run=data.get("was_manual_run"),
            circuit_id=data.get("circuit_id"),
            success=data.get("success"),
            outcome=IrrigationOutcome(data.get("outcome")),
            start_time=datetime.fromisoformat(data.get("start_time")) if data.get("start_time") else None,
            completed_duration=data.get("completed_duration"),
            target_duration=data.get("target_duration"),
            actual_water_amount=data.get("actual_water_amount"),
            target_water_amount=data.get("target_water_amount"),
            error=data.get("error")
            ,
            base_water_amount=data.get("base_water_amount"),
            standard_conditions_solar=data.get("standard_conditions_solar"),
            standard_conditions_rain=data.get("standard_conditions_rain"),
            standard_conditions_temp=data.get("standard_conditions_temp"),
            actual_solar=data.get("actual_solar"),
            actual_rain=data.get("actual_rain"),
            actual_temp=data.get("actual_temp"),
            carry_over_applied=data.get("carry_over_applied", False),
            even_area_mode=data.get("even_area_mode"),
            dynamic_interval_enabled=data.get("dynamic_interval_enabled"),
            irrigation_volume_threshold_percent=data.get("irrigation_volume_threshold_percent")
        )
