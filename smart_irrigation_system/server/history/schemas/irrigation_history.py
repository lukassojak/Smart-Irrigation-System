from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum



class IrrigationOutcome(str, Enum):
    """High-level result state of an irrigation attempt."""
    SUCCESS = "success"          # Irrigation completed successfully
    FAILED = "failed"            # Irrigation failed due to an error
    STOPPED = "stopped"          # Irrigation was manually stopped by the user
    INTERRUPTED = "interrupted"   # Irrigation was interrupted (e.g., power loss)
    SKIPPED = "skipped"          # Irrigation was skipped (e.g., due to conditions)


# ---- Pydantic Schemas for API ----

class IrrigationRecordInput(BaseModel):
    """Input model for a single irrigation record from the node."""
    circuit_id: int = Field(..., description="Circuit/zone ID")
    start_time: Optional[datetime] = Field(None, description="When irrigation started")
    outcome: str = Field(..., description="Outcome: success, failed, stopped, interrupted, skipped")
    was_manual_run: Optional[bool] = Field(None, description="Whether irrigation was started manually")
    success: Optional[bool] = Field(None, description="Whether the irrigation attempt was considered successful")
    completed_duration: Optional[int] = Field(None, description="Actual duration in seconds")
    target_duration: Optional[int] = Field(None, description="Target duration in seconds")
    actual_water_amount: Optional[float] = Field(None, description="Actual water used in liters")
    target_water_amount: Optional[float] = Field(None, description="Target water amount in liters")
    reason: Optional[str] = Field(None, description="Reason if outcome is interrupted, skipped, or failed")
    # Extended fields
    base_water_amount: Optional[float] = Field(None, description="Base water amount before corrections (liters)")
    standard_conditions_solar: Optional[float] = Field(None, description="Standard conditions: solar_total")
    standard_conditions_rain: Optional[float] = Field(None, description="Standard conditions: rain_mm")
    standard_conditions_temp: Optional[float] = Field(None, description="Standard conditions: temperature_celsius")
    actual_solar: Optional[float] = Field(None, description="Actual solar value used by node")
    actual_rain: Optional[float] = Field(None, description="Actual rain value used by node")
    actual_temp: Optional[float] = Field(None, description="Actual temperature value used by node")
    carry_over_applied: Optional[bool] = Field(False, description="Whether irrigation was carried over to next day")
    # even-area support
    even_area_mode: Optional[bool] = Field(None, description="Whether this circuit uses even-area (mm) mode")
    dynamic_interval_enabled: Optional[bool] = Field(None, description="Whether dynamic interval logic is enabled")
    irrigation_volume_threshold_percent: Optional[int] = Field(None, description="Threshold percent for carry-over logic")
    target_mm: Optional[float] = Field(None, description="Target in mm when even_area_mode is true")
    actual_mm: Optional[float] = Field(None, description="Actual delivered mm when even_area_mode is true")


class IrrigationHistoryUploadRequest(BaseModel):
    """Request model for uploading irrigation history from a node."""
    node_id: int = Field(..., description="Node ID")
    records: List[IrrigationRecordInput] = Field(..., description="List of irrigation records")


class IrrigationHistoryUploadResponse(BaseModel):
    """Response after uploading history."""
    uploaded_count: int
    message: str


class IrrigationHistoryRecord(BaseModel):
    """Represents a single irrigation history record."""
    id: int
    node_id: int
    circuit_id: int
    outcome: IrrigationOutcome
    zone_deleted: bool
    start_time: Optional[datetime] = None
    was_manual_run: Optional[bool] = None
    success: Optional[bool] = None
    target_duration: Optional[int] = None
    completed_duration: Optional[int] = None
    target_water_amount: Optional[float] = None
    actual_water_amount: Optional[float] = None
    reason: Optional[str] = None
    base_water_amount: Optional[float] = None
    standard_conditions_solar: Optional[float] = None
    standard_conditions_rain: Optional[float] = None
    standard_conditions_temp: Optional[float] = None
    actual_solar: Optional[float] = None
    actual_rain: Optional[float] = None
    actual_temp: Optional[float] = None
    carry_over_applied: Optional[bool] = None
    even_area_mode: Optional[bool] = None
    dynamic_interval_enabled: Optional[bool] = None
    irrigation_volume_threshold_percent: Optional[int] = None
    target_mm: Optional[float] = None
    actual_mm: Optional[float] = None
    zone_name: Optional[str] = None

class IrrigationHistoryReadResponse(BaseModel):
    """Response model for reading irrigation history records."""
    records: list[IrrigationHistoryRecord]
    total_records: int = Field(..., description="Total matching records in DB for the filters (no limit)")
    returned_records: int = Field(..., description="Number of records returned in this response")
    success_rate: float = Field(..., description="Fraction of total records that are successful")
    total_water: float = Field(..., description="Total actual water amount (liters) across all matching records")


class IrrigationHistoryReadRequest(BaseModel):
    node_id: Optional[int] = Field(None, description="Node ID to filter")
    circuit_id: Optional[int] = Field(None, description="Circuit ID to filter")
    limit: int = Field(100, description="Maximum number of records to return")
    include_deleted_zones: bool = Field(False, description="Whether to include records from deleted zones")