from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Column, JSON


class GlobalConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    standard_conditions: dict = Field(default_factory=dict, sa_column=Column(JSON))
    correction_factors: dict = Field(default_factory=dict, sa_column=Column(JSON))
    weather_api: dict = Field(default_factory=dict, sa_column=Column(JSON))

    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
