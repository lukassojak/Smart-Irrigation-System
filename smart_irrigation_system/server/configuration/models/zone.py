from sqlmodel import SQLModel, Field, Relationship, Column, JSON

from smart_irrigation_system.server.configuration.domain.domain import IrrigationMode


class Zone(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    node_id: int = Field(foreign_key="node.id")

    name: str = Field(index=True)
    relay_pin: int
    enabled: bool = True

    irrigation_mode: IrrigationMode

    # nested configurations stored as JSON
    local_correction_factors: dict | None = Field(default=None, sa_column=Column(JSON))
    frequency_settings: dict | None = Field(default=None, sa_column=Column(JSON))
    fallback_strategy: dict | None = Field(default=None, sa_column=Column(JSON))
    irrigation_configuration: dict | None = Field(default=None, sa_column=Column(JSON))
    emitters_configuration: dict | None = Field(default=None, sa_column=Column(JSON))

    node: "Node" = Relationship(
        back_populates="zones"
    )
