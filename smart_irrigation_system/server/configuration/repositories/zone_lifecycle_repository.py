from datetime import datetime

from sqlmodel import Session, select

from smart_irrigation_system.server.configuration.models.zone_lifecycle import ZoneLifecycle


class ZoneLifecycleRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, lifecycle: ZoneLifecycle) -> ZoneLifecycle:
        self.session.add(lifecycle)
        self.session.flush()
        return lifecycle

    def get_active(self, node_id: int, zone_id: int) -> ZoneLifecycle | None:
        statement = (
            select(ZoneLifecycle)
            .where(
                ZoneLifecycle.node_id == node_id,
                ZoneLifecycle.zone_id == zone_id,
                ZoneLifecycle.deleted_at.is_(None),
            )
            .order_by(ZoneLifecycle.created_at.desc())
        )
        return self.session.exec(statement).first()

    def get_applicable(self, node_id: int, zone_id: int, start_time: datetime) -> ZoneLifecycle | None:
        statement = (
            select(ZoneLifecycle)
            .where(
                ZoneLifecycle.node_id == node_id,
                ZoneLifecycle.zone_id == zone_id,
                ZoneLifecycle.created_at <= start_time,
                (ZoneLifecycle.deleted_at.is_(None)) | (ZoneLifecycle.deleted_at > start_time),
            )
            .order_by(ZoneLifecycle.created_at.desc())
        )
        return self.session.exec(statement).first()

    def mark_deleted(self, node_id: int, zone_id: int, deleted_at: datetime) -> ZoneLifecycle | None:
        lifecycle = self.get_active(node_id, zone_id)
        if not lifecycle:
            return None

        lifecycle.deleted_at = deleted_at
        self.session.flush()
        return lifecycle