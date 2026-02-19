from pydantic import BaseModel, ConfigDict

from datetime import datetime


from smart_irrigation_system.server.configuration.schemas.zone import ZoneRead
from smart_irrigation_system.server.configuration.schemas.logging import Logging
from smart_irrigation_system.server.configuration.schemas.hardware import HardwareConfiguration
from smart_irrigation_system.server.configuration.schemas.irrigation import (
    IrrigationLimits,
    Automation,
    BatchStrategy
)


class NodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str | None = None
    last_updated: datetime
    version: str | None = None
    hardware: HardwareConfiguration
    irrigation_limits: IrrigationLimits
    automation: Automation
    batch_strategy: BatchStrategy
    logging: Logging
    zones: list[ZoneRead]


class NodeCreate(BaseModel):
    name: str
    location: str | None = None 
    hardware: HardwareConfiguration
    irrigation_limits: IrrigationLimits
    automation: Automation
    batch_strategy: BatchStrategy
    logging: Logging


class NodeUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    hardware: HardwareConfiguration | None = None
    irrigation_limits: IrrigationLimits | None = None
    automation: Automation | None = None
    batch_strategy: BatchStrategy | None = None
    logging: Logging | None = None


class NodeListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str | None = None