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
    start_time: datetime = Field(index=True)  # When irrigation started (source of truth from node)
    created_at: datetime = Field(default_factory=datetime.utcnow)  # When record was synced to server
    
    # Outcome of the irrigation attempt
    outcome: str = Field(index=True)  # COMPLETED, INTERRUPTED, SKIPPED
    
    # Duration and volume data
    completed_duration: Optional[int] = None  # Actual duration in seconds (or None for SKIPPED)
    target_duration: Optional[int] = None  # Target duration in seconds
    actual_water_amount: Optional[float] = None  # Actual water used in liters (or None for SKIPPED)
    target_water_amount: Optional[float] = None  # Target water amount in liters
    
    # Additional metadata
    reason: Optional[str] = None  # Reason if outcome is INTERRUPTED or SKIPPED
