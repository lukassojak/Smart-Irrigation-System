from datetime import datetime, timezone
from smart_irrigation_system.server.runtime.schemas.live import (
    LiveResponse,
    ZoneLive,
    Alert,
    CurrentTask,
    Overview,
    ZoneStatus,
    AlertType
)


def get_live_snapshot() -> LiveResponse:
    """Simulate retrieval of live status snapshot for all zones, alerts, and current tasks."""
    # In a real implementation, this would query the database or in-memory state to get real data.
    now = datetime.now(timezone.utc)

    # Simulated zone statuses
    zones = [
        ZoneLive(id=1, name="Orchard", status=ZoneStatus.IRRIGATING, enabled=True, online=True, last_run=now.replace(hour=18, minute=30, second=0), progress_percent=42),
        ZoneLive(id=2, name="South Lawn", status=ZoneStatus.IDLE, enabled=True, online=True, last_run=None, progress_percent=None),
        ZoneLive(id=3, name="Greenhouse", status=ZoneStatus.IDLE, enabled=False, online=True, last_run=None, progress_percent=None),
        ZoneLive(id=4, name="Vegetable Patch", status=ZoneStatus.ERROR, enabled=True, online=True, last_run=None, progress_percent=None),
        ZoneLive(id=5, name="Poolside pots", status=ZoneStatus.OFFLINE, enabled=True, online=False, last_run=None, progress_percent=None)
    ]
    
    # Simulated alerts
    alerts = [
        Alert(id=1, type=AlertType.WARNING, title="Low Water Pressure", message="Water pressure is below threshold in Zone 5.", timestamp=now.replace(hour=12, minute=15, second=0)),
        Alert(id=2, type=AlertType.ERROR, title="Sensor Failure", message="Soil moisture sensor failed in Zone 4.", timestamp=now.replace(hour=11, minute=45, second=35))
    ]
    
    # Simulated current tasks
    current_tasks = [
        CurrentTask(id=1, zone_name="Zone 1", progress_percent=42, current_volume=23.85, target_volume=56.79, remaining_minutes=17)
    ]

    overview = Overview(
        zones_online=sum(1 for z in zones if z.online),
        total_zones=len(zones),
        warnings=sum(1 for a in alerts if a.type == AlertType.WARNING),
        errors=sum(1 for a in alerts if a.type == AlertType.ERROR)
    )
    
    return LiveResponse(
        overview=overview,
        zones=zones,
        alerts=alerts,
        current_tasks=current_tasks,
        last_update=datetime.now(timezone.utc)
    )