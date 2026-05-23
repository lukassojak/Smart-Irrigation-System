from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class ZoneLifecycle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    node_id: int = Field(index=True)
    zone_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    deleted_at: datetime | None = Field(default=None, index=True)