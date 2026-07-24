"""Database models for irrigation history tracking."""

from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional


class IrrigationHistory(SQLModel, table=True):
    """Stores historical records of every irrigation attempt for analytics and debugging."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign key to node (from which node this record came)
    node_id: int = Field(foreign_key="node.id", index=True)
    
    # Circuit/Zone ID on the node
    circuit_id: int = Field(index=True)

    # Whether the source zone was already deleted when this record was stored
    zone_deleted: bool = Field(default=False, index=True)
    
    # Timestamps
    start_time: Optional[datetime] = Field(default=None, index=True)  # When irrigation started (source of truth from node)
    created_at: datetime = Field(default_factory=datetime.utcnow)  # When record was synced to server
    
    # Outcome of the irrigation attempt
    outcome: str = Field(index=True)  # SUCCESS, FAILED, STOPPED, SKIPPED, INTERRUPTED
    success: Optional[bool] = Field(default=None, index=True)
    was_manual_run: Optional[bool] = Field(default=None)
    
    # Duration and volume data
    completed_duration: Optional[int] = None  # Actual duration in seconds (or None for SKIPPED)
    target_duration: Optional[int] = None  # Target duration in seconds
    actual_water_amount: Optional[float] = None  # Actual water used in liters (or None for SKIPPED)
    target_water_amount: Optional[float] = None  # Target water amount in liters
    # base value before weather corrections
    base_water_amount: Optional[float] = None
    # standard conditions snapshot from node when computing irrigation
    standard_conditions_solar: Optional[float] = None
    standard_conditions_rain: Optional[float] = None
    standard_conditions_temp: Optional[float] = None
    # actual observed weather values used for the computation
    actual_solar: Optional[float] = None
    actual_rain: Optional[float] = None
    actual_temp: Optional[float] = None
    # carry-over flag: whether irrigation was deferred to next day
    carry_over_applied: Optional[bool] = Field(default=False)
    dynamic_interval_enabled: Optional[bool] = Field(default=None)
    irrigation_volume_threshold_percent: Optional[int] = Field(default=None)
    
    # Additional metadata
    reason: Optional[str] = None  # Reason if outcome is INTERRUPTED or SKIPPED
    # even-area mode fields
    even_area_mode: Optional[bool] = Field(default=False)
    target_mm: Optional[float] = None
    actual_mm: Optional[float] = None
