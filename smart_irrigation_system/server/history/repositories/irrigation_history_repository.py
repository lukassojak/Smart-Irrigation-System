from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlmodel import Session, select
from sqlalchemy import func

from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory
from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory as HistoryModel
from smart_irrigation_system.server.configuration.models.zone import Zone


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
    ) -> List[Dict[str, Any]]:
        query = select(HistoryModel)
        if node_id is not None:
            query = query.where(HistoryModel.node_id == node_id)
        if circuit_id is not None:
            query = query.where(HistoryModel.circuit_id == circuit_id)
        if outcome is not None:
            query = query.where(HistoryModel.outcome == outcome)
        if not include_deleted_zones:
            query = query.where(HistoryModel.zone_deleted.is_(False))
        query = query.order_by(HistoryModel.start_time.desc()).limit(limit)
        rows = self.session.exec(query).all()
        return [self._to_dict(row) for row in rows]

    def get_by_unique(
        self,
        node_id: int,
        circuit_id: int,
        start_time: Optional[object] = None,
    ) -> Optional[Dict[str, Any]]:
        query = select(HistoryModel).where(HistoryModel.node_id == node_id, HistoryModel.circuit_id == circuit_id)
        if start_time is not None:
            query = query.where(HistoryModel.start_time == start_time)
        row = self.session.exec(query).first()
        return self._to_dict(row) if row else None

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        row = self.session.get(HistoryModel, record_id)
        return self._to_dict(row) if row else None

    def delete_record(self, node_id: int, circuit_id: int, start_time: Optional[object] = None) -> int:
        query = select(HistoryModel).where(HistoryModel.node_id == node_id, HistoryModel.circuit_id == circuit_id)
        if start_time is not None:
            query = query.where(HistoryModel.start_time == start_time)
        row = self.session.exec(query).first()
        if row is None:
            return 0
        self.session.delete(row)
        self.session.commit()
        return 1

    def delete_record_by_id(self, record_id: int) -> int:
        row = self.session.get(HistoryModel, record_id)
        if row is None:
            return 0
        self.session.delete(row)
        self.session.commit()
        return 1

    def delete_records(self, node_id: Optional[int] = None, circuit_id: Optional[int] = None) -> int:
        query = select(HistoryModel)
        if node_id is not None:
            query = query.where(HistoryModel.node_id == node_id)
        if circuit_id is not None:
            query = query.where(HistoryModel.circuit_id == circuit_id)
        rows = self.session.exec(query).all()
        for row in rows:
            self.session.delete(row)
        self.session.commit()
        return len(rows)

    def get_zone_name(self, circuit_id: int) -> Optional[str]:
        zone = self.session.exec(select(Zone).where(Zone.id == circuit_id)).first()
        return zone.name if zone else None

    def _to_dict(self, row: Optional[HistoryModel]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return {
            "id": row.id,
            "node_id": row.node_id,
            "circuit_id": row.circuit_id,
            "start_time": row.start_time,
            "outcome": row.outcome,
            "target_water_amount": row.target_water_amount,
            "actual_water_amount": row.actual_water_amount,
            "base_water_amount": row.base_water_amount,
            "standard_conditions_solar": row.standard_conditions_solar,
            "standard_conditions_rain": row.standard_conditions_rain,
            "standard_conditions_temp": row.standard_conditions_temp,
            "actual_solar": row.actual_solar,
            "actual_rain": row.actual_rain,
            "actual_temp": row.actual_temp,
            "completed_duration": row.completed_duration,
            "target_duration": row.target_duration,
            "carry_over_applied": row.carry_over_applied,
            "dynamic_interval_enabled": row.dynamic_interval_enabled,
            "irrigation_volume_threshold_percent": row.irrigation_volume_threshold_percent,
            "even_area_mode": row.even_area_mode,
            "was_manual_run": row.was_manual_run,
            "zone_deleted": row.zone_deleted,
            "reason": row.reason,
            "success": row.success,
            "target_mm": row.target_mm,
            "actual_mm": row.actual_mm,
            "created_at": row.created_at,
        }

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

    def avg_correction(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
    ) -> float:
        correction_expr = 1 - (
            IrrigationHistory.target_water_amount / func.nullif(IrrigationHistory.base_water_amount, 0)
        )
        statement = select(func.avg(correction_expr)).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        result = self.session.exec(statement).one()
        val = result[0] if isinstance(result, tuple) else result
        return float(val or 0.0)

    def create(self, record: IrrigationHistory) -> IrrigationHistory:
        self.session.add(record)
        self.session.flush()
        return record
