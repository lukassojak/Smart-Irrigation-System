from sqlmodel import SQLModel, Field, Relationship, Column, JSON

from datetime import datetime, timezone
from smart_irrigation_system.server.configuration.models.zone import Zone


CONFIG_SYNC_PENDING = "PENDING"
CONFIG_SYNC_PUSHED = "PUSHED"


class Node(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True) # Should be auto-incrementing

    name: str = Field(index=True)
    location: str | None = None
    hardware_uid: str | None = Field(default=None, index=True, unique=True)
    version: str | None = None
    config_sync_status: str = Field(default=CONFIG_SYNC_PENDING, index=True)

    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # should be updated on each change

    # nested configurations stored as JSON
    hardware: dict | None = Field(default=None, sa_column=Column(JSON))
    irrigation_limits: dict | None = Field(default=None, sa_column=Column(JSON))
    automation: dict | None = Field(default=None, sa_column=Column(JSON))
    batch_strategy: dict | None = Field(default=None, sa_column=Column(JSON))
    logging: dict | None = Field(default=None, sa_column=Column(JSON))

    zones: list[Zone] = Relationship(
        back_populates="node",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

