from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlmodel import Session, select
from sqlalchemy import func

from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory
from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory as HistoryModel
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.models.zone_lifecycle import ZoneLifecycle


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
        range_days: Optional[int] = None,
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
        query = self._apply_range_days(query, range_days)
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

    def upload_records(self, node_id: int, records: List[dict]) -> Tuple[int, int]:
        uploaded_count = 0
        skipped_count = 0
        seen_keys = set()

        for record in records:
            payload = self._normalize_record_payload(record)
            circuit_id = payload.get("circuit_id")
            if circuit_id is None:
                raise ValueError("Record is missing circuit_id")

            start_time = payload.get("start_time")
            record_key = (node_id, circuit_id, start_time)
            if record_key in seen_keys:
                skipped_count += 1
                continue
            seen_keys.add(record_key)

            existing = self.get_by_unique(node_id=node_id, circuit_id=circuit_id, start_time=start_time)
            if existing:
                skipped_count += 1
                continue

            zone_deleted = self._is_zone_deleted(node_id=node_id, zone_id=circuit_id, start_time=start_time)
            history_record = IrrigationHistory(
                node_id=node_id,
                circuit_id=circuit_id,
                zone_deleted=zone_deleted,
                start_time=start_time,
                outcome=payload.get("outcome"),
                success=payload.get("success"),
                was_manual_run=payload.get("was_manual_run"),
                completed_duration=payload.get("completed_duration"),
                target_duration=payload.get("target_duration"),
                actual_water_amount=payload.get("actual_water_amount"),
                target_water_amount=payload.get("target_water_amount"),
                base_water_amount=payload.get("base_water_amount"),
                standard_conditions_solar=payload.get("standard_conditions_solar"),
                standard_conditions_rain=payload.get("standard_conditions_rain"),
                standard_conditions_temp=payload.get("standard_conditions_temp"),
                actual_solar=payload.get("actual_solar"),
                actual_rain=payload.get("actual_rain"),
                actual_temp=payload.get("actual_temp"),
                carry_over_applied=payload.get("carry_over_applied", False),
                dynamic_interval_enabled=payload.get("dynamic_interval_enabled"),
                irrigation_volume_threshold_percent=payload.get("irrigation_volume_threshold_percent"),
                reason=payload.get("reason"),
                even_area_mode=payload.get("even_area_mode"),
                target_mm=payload.get("target_mm"),
                actual_mm=payload.get("actual_mm"),
            )
            self.session.add(history_record)
            uploaded_count += 1

        self.session.commit()
        return uploaded_count, skipped_count

    def _normalize_record_payload(self, record: Any) -> Dict[str, Any]:
        if isinstance(record, dict):
            return dict(record)
        if hasattr(record, "model_dump"):
            return record.model_dump()
        if hasattr(record, "dict"):
            return record.dict()
        raise TypeError(f"Unsupported record type: {type(record)!r}")

    def _is_zone_deleted(self, node_id: int, zone_id: int, start_time: Optional[datetime]) -> bool:
        if start_time is None:
            return False

        lifecycles = self.session.exec(
            select(ZoneLifecycle).where(
                ZoneLifecycle.node_id == node_id,
                ZoneLifecycle.zone_id == zone_id,
            )
        ).all()

        if not lifecycles:
            return False

        applicable_lifecycles = [
            lifecycle for lifecycle in lifecycles
            if lifecycle.created_at is not None and lifecycle.created_at <= start_time
        ]
        if not applicable_lifecycles:
            return False

        latest_lifecycle = max(applicable_lifecycles, key=lambda lifecycle: lifecycle.created_at)

        if any(
            lifecycle.created_at is not None and lifecycle.created_at > start_time
            for lifecycle in lifecycles
        ):
            return True

        return (
            latest_lifecycle.deleted_at is not None
            and latest_lifecycle.deleted_at <= start_time
        )

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
        range_days: Optional[int] = None,
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

        statement = self._apply_range_days(statement, range_days)

        return int(self.session.exec(statement).one())

    def count_successful_records(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
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

        statement = self._apply_range_days(statement, range_days)

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
        range_days: Optional[int] = None,
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

        statement = self._apply_range_days(statement, range_days)

        result = self.session.exec(statement).one()
        # result may be (None,) if no rows
        val = result[0] if isinstance(result, tuple) else result
        return float(val or 0.0)

    def count_manual_runs(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
    ) -> int:
        statement = select(func.count()).select_from(IrrigationHistory).where(
            IrrigationHistory.was_manual_run.is_(True)
        )

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        statement = self._apply_range_days(statement, range_days)

        return int(self.session.exec(statement).one())

    def count_outcome_records(
        self,
        outcome_value: str,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
    ) -> int:
        statement = select(func.count()).select_from(IrrigationHistory).where(
            IrrigationHistory.outcome == outcome_value
        )

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        statement = self._apply_range_days(statement, range_days)

        return int(self.session.exec(statement).one())

    def get_record_time_bounds(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        statement = select(
            func.min(IrrigationHistory.start_time),
            func.max(IrrigationHistory.start_time),
        ).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        statement = self._apply_range_days(statement, range_days)

        first_record_at, last_record_at = self.session.exec(statement).one()
        return first_record_at, last_record_at

    def get_daily_water_trend(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        statement = select(
            func.date(IrrigationHistory.start_time).label("date"),
            func.coalesce(func.sum(IrrigationHistory.actual_water_amount), 0).label("water"),
            func.count(IrrigationHistory.id).label("runs"),
        ).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        statement = self._apply_range_days(statement, range_days)

        statement = statement.group_by(func.date(IrrigationHistory.start_time))
        statement = statement.order_by(func.date(IrrigationHistory.start_time).asc())

        rows = self.session.exec(statement).all()
        points = [
            {
                "date": row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0]),
                "water": float(row[1] or 0.0),
                "runs": int(row[2] or 0),
            }
            for row in rows
        ]

        if not range_days:
            return points

        points_by_date: Dict[str, Dict[str, Any]] = {point["date"]: point for point in points}
        today = datetime.utcnow().date()
        first_day = today - timedelta(days=range_days - 1)

        complete_points: List[Dict[str, Any]] = []
        for offset in range(range_days):
            current_day = first_day + timedelta(days=offset)
            current_key = current_day.isoformat()
            complete_points.append(
                points_by_date.get(
                    current_key,
                    {
                        "date": current_key,
                        "water": 0.0,
                        "runs": 0,
                    },
                )
            )

        return complete_points

    def get_outcome_breakdown(
        self,
        node_id: Optional[int] = None,
        circuit_ids: Optional[List[int]] = None,
        include_deleted_zones: bool = False,
        range_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        statement = select(
            IrrigationHistory.outcome,
            func.count(IrrigationHistory.id),
        ).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_ids:
            statement = statement.where(IrrigationHistory.circuit_id.in_(circuit_ids))

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        statement = self._apply_range_days(statement, range_days)
        statement = statement.group_by(IrrigationHistory.outcome)
        statement = statement.order_by(func.count(IrrigationHistory.id).desc())

        rows = self.session.exec(statement).all()
        return [
            {"name": row[0], "value": int(row[1] or 0)}
            for row in rows
        ]

    def get_zone_water_distribution(
        self,
        node_id: Optional[int] = None,
        circuit_ids: Optional[List[int]] = None,
        include_deleted_zones: bool = False,
        range_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        statement = select(
            IrrigationHistory.circuit_id,
            func.sum(IrrigationHistory.actual_water_amount),
            func.count(IrrigationHistory.id),
        ).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_ids:
            statement = statement.where(IrrigationHistory.circuit_id.in_(circuit_ids))

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        statement = self._apply_range_days(statement, range_days)
        statement = statement.group_by(IrrigationHistory.circuit_id)
        statement = statement.order_by(func.sum(IrrigationHistory.actual_water_amount).desc())

        rows = self.session.exec(statement).all()
        return [
            {
                "circuit_id": int(row[0]),
                "zone_name": self.get_zone_name(int(row[0])) if row[0] is not None else None,
                "water": float(row[1] or 0.0),
                "runs": int(row[2] or 0),
            }
            for row in rows
        ]

    def get_zone_correction_trend(
        self,
        circuit_id: Optional[int] = None,
        node_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        range_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        correction_expr = (
            IrrigationHistory.target_water_amount / func.nullif(IrrigationHistory.base_water_amount, 0)
        ) - 1
        statement = select(
            func.date(IrrigationHistory.start_time).label("date"),
            func.avg(correction_expr).label("correction"),
            func.count(IrrigationHistory.id).label("runs"),
        ).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        statement = statement.where(IrrigationHistory.was_manual_run.is_(False))
        statement = statement.where(IrrigationHistory.base_water_amount.is_not(None))
        statement = statement.where(IrrigationHistory.base_water_amount != 0)
        statement = self._apply_range_days(statement, range_days)
        statement = statement.group_by(func.date(IrrigationHistory.start_time))
        statement = statement.order_by(func.date(IrrigationHistory.start_time).asc())

        rows = self.session.exec(statement).all()
        return [
            {
                "date": row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0]),
                "correction": float(row[1] or 0.0),
                "runs": int(row[2] or 0),
            }
            for row in rows
        ]

    def _apply_range_days(self, statement, range_days: Optional[int]):
        if range_days is None:
            return statement

        cutoff = datetime.utcnow() - timedelta(days=range_days)
        return statement.where(
            IrrigationHistory.start_time.is_not(None),
            IrrigationHistory.start_time >= cutoff,
        )

    def avg_correction(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
    ) -> float:
        correction_expr = (
            IrrigationHistory.target_water_amount / func.nullif(IrrigationHistory.base_water_amount, 0)
        ) - 1
        statement = select(func.avg(correction_expr)).select_from(IrrigationHistory)

        if node_id is not None:
            statement = statement.where(IrrigationHistory.node_id == node_id)

        if circuit_id is not None:
            statement = statement.where(IrrigationHistory.circuit_id == circuit_id)

        if not include_deleted_zones:
            statement = statement.where(IrrigationHistory.zone_deleted.is_(False))

        if outcome is not None:
            statement = statement.where(IrrigationHistory.outcome == outcome)

        statement = self._apply_range_days(statement, range_days)

        statement = statement.where(IrrigationHistory.was_manual_run.is_(False))
        statement = statement.where(IrrigationHistory.base_water_amount.is_not(None))
        statement = statement.where(IrrigationHistory.base_water_amount != 0)

        result = self.session.exec(statement).one()
        val = result[0] if isinstance(result, tuple) else result
        return float(val or 0.0)

    def create(self, record: IrrigationHistory) -> IrrigationHistory:
        self.session.add(record)
        self.session.flush()
        return record
