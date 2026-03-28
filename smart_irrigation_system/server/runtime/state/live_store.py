
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading

from smart_irrigation_system.server.runtime.schemas.live import AlertType, ZoneStatus


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class NodeRuntimeState:
    node_id: int
    node_name: str | None = None
    last_seen_at: datetime | None = None
    first_seen_at: datetime | None = None
    ever_seen: bool = False


@dataclass
class ZoneRuntimeState:
    zone_id: int
    node_id: int
    zone_name: str
    enabled: bool = True
    status: ZoneStatus = ZoneStatus.OFFLINE
    progress_percent: float | None = None
    last_run: datetime | None = None
    last_update_at: datetime | None = None


@dataclass
class CurrentTaskRuntimeState:
    id: int
    zone_id: int | None
    zone_name: str
    progress_percent: float
    current_volume: float
    target_volume: float
    remaining_minutes: int
    last_update_at: datetime = field(default_factory=utcnow)


@dataclass
class AlertRuntimeState:
    id: int
    type: AlertType
    title: str
    message: str
    timestamp: datetime = field(default_factory=utcnow)


@dataclass
class RuntimeLiveSnapshot:
    started_at: datetime
    last_update_at: datetime
    nodes: dict[int, NodeRuntimeState]
    zones: dict[int, ZoneRuntimeState]
    current_tasks: dict[int, CurrentTaskRuntimeState]
    alerts: list[AlertRuntimeState]


class RuntimeLiveStore:
    """Thread-safe in-memory runtime state used by live projection endpoints."""

    def __init__(self):
        self._lock = threading.RLock()
        self.started_at = utcnow()
        self._last_update_at = self.started_at
        self._nodes: dict[int, NodeRuntimeState] = {}
        self._zones: dict[int, ZoneRuntimeState] = {}
        self._current_tasks: dict[int, CurrentTaskRuntimeState] = {}
        self._alerts: list[AlertRuntimeState] = []
        self._next_alert_id = 1

    def register_expected_topology(self, expected_nodes: list[dict]) -> None:
        """Initialize known nodes and zones from config DB into an offline baseline."""
        with self._lock:
            self._nodes.clear()
            self._zones.clear()
            self._current_tasks.clear()

            for node in expected_nodes:
                node_id = int(node["node_id"])
                self._nodes[node_id] = NodeRuntimeState(
                    node_id=node_id,
                    node_name=node.get("node_name"),
                )

                for zone in node.get("zones", []):
                    zone_id = int(zone["zone_id"])
                    self._zones[zone_id] = ZoneRuntimeState(
                        zone_id=zone_id,
                        node_id=node_id,
                        zone_name=zone.get("zone_name", f"Zone {zone_id}"),
                        enabled=bool(zone.get("enabled", True)),
                    )

            self._last_update_at = utcnow()

    def upsert_node_heartbeat(self, node_id: int, seen_at: datetime | None = None) -> None:
        seen_at = seen_at or utcnow()
        with self._lock:
            node_state = self._nodes.get(node_id)
            if node_state is None:
                node_state = NodeRuntimeState(node_id=node_id)
                self._nodes[node_id] = node_state

            node_state.last_seen_at = seen_at
            if not node_state.ever_seen:
                node_state.first_seen_at = seen_at
                node_state.ever_seen = True

            self._last_update_at = seen_at

    def upsert_zone_state(
        self,
        node_id: int,
        zone_id: int,
        status: ZoneStatus,
        progress_percent: float | None = None,
        last_run: datetime | None = None,
        zone_name: str | None = None,
        enabled: bool | None = None,
        seen_at: datetime | None = None,
    ) -> None:
        seen_at = seen_at or utcnow()
        with self._lock:
            self.upsert_node_heartbeat(node_id=node_id, seen_at=seen_at)

            zone_state = self._zones.get(zone_id)
            if zone_state is None:
                zone_state = ZoneRuntimeState(
                    zone_id=zone_id,
                    node_id=node_id,
                    zone_name=zone_name or f"Zone {zone_id}",
                    enabled=True if enabled is None else enabled,
                )
                self._zones[zone_id] = zone_state

            zone_state.node_id = node_id
            if zone_name:
                zone_state.zone_name = zone_name
            if enabled is not None:
                zone_state.enabled = enabled
            zone_state.status = status
            zone_state.progress_percent = progress_percent
            zone_state.last_run = last_run
            zone_state.last_update_at = seen_at
            self._last_update_at = seen_at

    def upsert_current_task(
        self,
        task_id: int,
        zone_name: str,
        progress_percent: float,
        current_volume: float,
        target_volume: float,
        remaining_minutes: int,
        zone_id: int | None = None,
        seen_at: datetime | None = None,
    ) -> None:
        seen_at = seen_at or utcnow()
        with self._lock:
            self._current_tasks[task_id] = CurrentTaskRuntimeState(
                id=task_id,
                zone_id=zone_id,
                zone_name=zone_name,
                progress_percent=progress_percent,
                current_volume=current_volume,
                target_volume=target_volume,
                remaining_minutes=remaining_minutes,
                last_update_at=seen_at,
            )
            self._last_update_at = seen_at

    def clear_current_task(self, task_id: int) -> None:
        with self._lock:
            self._current_tasks.pop(task_id, None)
            self._last_update_at = utcnow()

    def add_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        timestamp: datetime | None = None,
    ) -> int:
        timestamp = timestamp or utcnow()
        with self._lock:
            alert_id = self._next_alert_id
            self._next_alert_id += 1
            self._alerts.append(
                AlertRuntimeState(
                    id=alert_id,
                    type=alert_type,
                    title=title,
                    message=message,
                    timestamp=timestamp,
                )
            )
            self._last_update_at = timestamp
            return alert_id

    def get_snapshot(self) -> RuntimeLiveSnapshot:
        with self._lock:
            return RuntimeLiveSnapshot(
                started_at=self.started_at,
                last_update_at=self._last_update_at,
                nodes=deepcopy(self._nodes),
                zones=deepcopy(self._zones),
                current_tasks=deepcopy(self._current_tasks),
                alerts=deepcopy(self._alerts),
            )
