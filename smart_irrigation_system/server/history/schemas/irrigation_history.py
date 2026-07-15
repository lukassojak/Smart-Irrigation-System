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
    start_time: datetime = Field(..., description="When irrigation started")
    outcome: str = Field(..., description="Outcome: success, failed, stopped, interrupted, skipped")
    completed_duration: Optional[int] = Field(None, description="Actual duration in seconds")
    target_duration: Optional[int] = Field(None, description="Target duration in seconds")
    actual_water_amount: Optional[float] = Field(None, description="Actual water used in liters")
    target_water_amount: Optional[float] = Field(None, description="Target water amount in liters")
    reason: Optional[str] = Field(None, description="Reason if outcome is interrupted, skipped, or failed")


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
    start_time: datetime
    target_duration: Optional[int]
    completed_duration: Optional[int]
    target_water_amount: Optional[float]
    actual_water_amount: Optional[float]
    reason: Optional[str]

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