from typing import Optional, List

from sqlmodel import Session, select
from sqlalchemy import func

from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory


class IrrigationHistoryRepository:
    """Repository responsible for CRUD operations on IrrigationHistory records.

    This class intentionally does not commit transactions; callers manage
    transaction boundaries (flush / commit) as done across the codebase.
    """

    def __init__(self, session: Session):
        self.session = session

    def list_records(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        limit: int = 100,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
    ) -> List[IrrigationHistory]:
        statement = select(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        statement = statement.order_by(IrrigationHistory.start_time.desc()).limit(limit)

        return self.session.exec(statement).all()

    def get_by_unique(self, node_id: int, circuit_id: int, start_time) -> Optional[IrrigationHistory]:
        statement = (
            select(IrrigationHistory)
            .where(
                IrrigationHistory.node_id == node_id,
                IrrigationHistory.circuit_id == circuit_id,
                IrrigationHistory.start_time == start_time,
            )
        )
        return self.session.exec(statement).first()

    def count_records(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
    ) -> int:
        statement = select(func.count()).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        return int(self.session.exec(statement).one())

    def count_successful_records(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
    ) -> int:
        # successful = not (failed or interrupted)
        statement = select(func.count()).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        statement = statement.where(
            (IrrigationHistory.outcome != 'failed') & (IrrigationHistory.outcome != 'interrupted')
        )

        return int(self.session.exec(statement).one())

    def sum_water(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
    ) -> float:
        statement = select(func.sum(IrrigationHistory.actual_water_amount)).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        result = self.session.exec(statement).one()
        # result may be (None,) if no rows
        val = result[0] if isinstance(result, tuple) else result
        return float(val or 0.0)

    def create(self, record: IrrigationHistory) -> IrrigationHistory:
        self.session.add(record)
        self.session.flush()
        return record

    def delete_records(self, node_id: Optional[int] = None, circuit_id: Optional[int] = None) -> int:
        statement = select(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        records = self.session.exec(statement).all()
        deleted = 0
        for r in records:
            self.session.delete(r)
            deleted += 1

        # caller decides about commit; flush so callers can see deletions
        self.session.flush()
        return deleted
