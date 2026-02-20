from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class ZoneStatus(str, Enum):
    IRRIGATING = "irrigating"
    IDLE = "idle"
    ERROR = "error"
    STOPPING = "stopping"
    OFFLINE = "offline"

class AlertType(str, Enum):
    WARNING = "warning"
    ERROR = "error"


# ========================= Response models for live status endpoints =========================

class Overview(BaseModel):
    zones_online: int
    total_zones: int
    warnings: int
    errors: int

class ZoneLive(BaseModel):
    id: int
    name: str
    status: ZoneStatus
    enabled: bool
    online: bool
    last_run: datetime | None = None
    progress_percent: float | None = None

class Alert(BaseModel):
    id: int
    type: AlertType
    title: str
    message: str
    timestamp: datetime

class CurrentTask(BaseModel):
    id: int
    zone_name: str
    progress_percent: float
    current_volume: float
    target_volume: float
    remaining_minutes: int

class LiveResponse(BaseModel):
    overview: Overview
    zones: list[ZoneLive]
    alerts: list[Alert]
    current_tasks: list[CurrentTask]
    last_update: datetime


