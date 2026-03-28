from datetime import datetime, timedelta, timezone
from sqlmodel import Session

from smart_irrigation_system.server.configuration.repositories.node_repository import NodeRepository
from smart_irrigation_system.server.configuration.repositories.zone_repository import ZoneRepository
from smart_irrigation_system.server.runtime.schemas.live import (
    LiveResponse,
    ZoneLive,
    Alert,
    CurrentTask,
    Overview,
    ZoneStatus,
    AlertType
)
from smart_irrigation_system.server.runtime.state.live_store import RuntimeLiveStore


class LiveService:
    def __init__(
        self,
        store: RuntimeLiveStore,
        # Node mqtt heartbeat publish around 5s
        # Server fallback status request around 10-15s
        # UI REST refresh (dashboard) around 2-3s
        connecting_timeout_seconds: int = 30,
        stale_timeout_seconds: int = 20,
        offline_timeout_seconds: int = 60,
    ):
        self.store = store
        self.connecting_timeout = timedelta(seconds=connecting_timeout_seconds)
        self.stale_timeout = timedelta(seconds=stale_timeout_seconds)
        self.offline_timeout = timedelta(seconds=offline_timeout_seconds)

    def _is_connecting(self, started_at: datetime, now: datetime, node_ever_seen: bool) -> bool:
        if node_ever_seen:
            return False
        return (now - started_at) <= self.connecting_timeout

    def _is_offline(self, now: datetime, node_last_seen: datetime | None) -> bool:
        if node_last_seen is None:
            return True
        return (now - node_last_seen) > self.offline_timeout

    def _is_stale(self, now: datetime, updated_at: datetime | None) -> bool:
        if updated_at is None:
            return True
        return (now - updated_at) > self.stale_timeout

    def get_live_snapshot(self) -> LiveResponse:
        now = datetime.now(timezone.utc)
        snapshot = self.store.get_snapshot()

        zones: list[ZoneLive] = []
        for zone_state in sorted(snapshot.zones.values(), key=lambda z: z.zone_id):
            node_state = snapshot.nodes.get(zone_state.node_id)
            node_last_seen = node_state.last_seen_at if node_state else None
            node_ever_seen = node_state.ever_seen if node_state else False

            connecting_to_node = self._is_connecting(
                started_at=snapshot.started_at,
                now=now,
                node_ever_seen=node_ever_seen,
            )
            offline = self._is_offline(now=now, node_last_seen=node_last_seen)
            stale = self._is_stale(now=now, updated_at=zone_state.last_update_at)

            if offline:
                status = ZoneStatus.OFFLINE
                online = False
                progress_percent = None
            else:
                status = zone_state.status
                online = True
                progress_percent = None if stale else zone_state.progress_percent

            zones.append(
                ZoneLive(
                    id=zone_state.zone_id,
                    name=zone_state.zone_name,
                    status=status,
                    enabled=zone_state.enabled,
                    online=online,
                    stale=stale,
                    connecting_to_node=connecting_to_node,
                    last_run=zone_state.last_run,
                    progress_percent=progress_percent,
                )
            )

        alerts = [
            Alert(
                id=a.id,
                type=a.type,
                title=a.title,
                message=a.message,
                timestamp=a.timestamp,
            )
            for a in sorted(snapshot.alerts, key=lambda x: x.timestamp, reverse=True)
        ]

        current_tasks: list[CurrentTask] = []
        for task in sorted(snapshot.current_tasks.values(), key=lambda t: t.id):
            task_stale = self._is_stale(now=now, updated_at=task.last_update_at)
            current_tasks.append(
                CurrentTask(
                    id=task.id,
                    zone_name=task.zone_name,
                    progress_percent=task.progress_percent,
                    current_volume=task.current_volume,
                    target_volume=task.target_volume,
                    remaining_minutes=task.remaining_minutes,
                    stale=task_stale,
                )
            )

        overview = Overview(
            zones_online=sum(1 for z in zones if z.online),
            total_zones=len(zones),
            warnings=sum(1 for a in alerts if a.type == AlertType.WARNING),
            errors=sum(1 for a in alerts if a.type == AlertType.ERROR),
        )

        return LiveResponse(
            overview=overview,
            zones=zones,
            alerts=alerts,
            current_tasks=current_tasks,
            last_update=snapshot.last_update_at,
        )


_runtime_live_store = RuntimeLiveStore()
_live_service = LiveService(store=_runtime_live_store)


def get_live_store() -> RuntimeLiveStore:
    return _runtime_live_store


def initialize_live_store_from_config(session: Session) -> None:
    node_repo = NodeRepository(session)
    zone_repo = ZoneRepository(session)

    expected_nodes: list[dict] = []
    for node in node_repo.list_all():
        zones = zone_repo.list_by_node(node.id)
        expected_nodes.append(
            {
                "node_id": node.id,
                "node_name": node.name,
                "zones": [
                    {
                        "zone_id": zone.id,
                        "zone_name": zone.name,
                        "enabled": zone.enabled,
                    }
                    for zone in zones
                ],
            }
        )

    _runtime_live_store.register_expected_topology(expected_nodes)


def get_live_snapshot() -> LiveResponse:
    return _live_service.get_live_snapshot()