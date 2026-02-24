from datetime import datetime, timezone
from smart_irrigation_system.server.runtime.schemas.today import (
    TodayResponse,
    TodayTask,
    TaskStatus,
    TodayOverview
)


def get_today_snapshot() -> TodayResponse:
    now = datetime.now(timezone.utc)

    tasks = [
        TodayTask(
            id=1,
            zone_id=3,
            zone_name="Orchard",
            scheduled_time=now.replace(hour=20, minute=0, second=0),
            expected_volume_liters=14.0,
            expected_adjustment_percent=34,
            status=TaskStatus.PLANNED
        ),
        TodayTask(
            id=2,
            zone_id=1,
            zone_name="South Lawn",
            scheduled_time=now.replace(hour=18, minute=30, second=0),
            expected_volume_liters=12.2,
            expected_adjustment_percent=29,
            status=TaskStatus.PLANNED
        ),
        TodayTask(
            id=3,
            zone_id=2,
            zone_name="Greenhouse",
            scheduled_time=now.replace(hour=12, minute=30, second=0),
            expected_volume_liters=4.52,
            expected_adjustment_percent=7,
            status=TaskStatus.COMPLETED
        ),
        TodayTask(
            id=4,
            zone_id=4,
            zone_name="Vegetable Patch",
            scheduled_time=now.replace(hour=17, minute=0, second=0),
            expected_volume_liters=8.75,
            expected_adjustment_percent=20,
            status=TaskStatus.IN_PROGRESS
        )
    ]

    overview = TodayOverview(
        tasks_total=len(tasks),
        tasks_planned=sum(1 for t in tasks if t.status == TaskStatus.PLANNED),
        tasks_in_progress=sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
        tasks_completed=sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
        total_expected_volume=sum(t.expected_volume_liters for t in tasks)
    )

    return TodayResponse(
        date=now,
        overview=overview,
        tasks=tasks,
        last_update=datetime.now(timezone.utc)
    )