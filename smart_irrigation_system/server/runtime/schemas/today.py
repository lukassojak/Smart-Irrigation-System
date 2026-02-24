from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ========================= Response models for today's data endpoints =========================

class TodayTask(BaseModel):
    id: int
    zone_id: int
    zone_name: str
    scheduled_time: datetime
    expected_volume_liters: float
    expected_adjustment_percent: float
    status: TaskStatus

class TodayOverview(BaseModel):
    tasks_total: int
    tasks_planned: int
    tasks_in_progress: int
    tasks_completed: int
    total_expected_volume: float

class TodayResponse(BaseModel):
    date: datetime
    overview: TodayOverview
    tasks: list[TodayTask]
    last_update: datetime
    