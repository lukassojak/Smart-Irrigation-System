from sqlmodel import Session

from smart_irrigation_system.server.configuration.domain.domain import IrrigationMode
from smart_irrigation_system.server.configuration.repositories.zone_repository import ZoneRepository
from smart_irrigation_system.server.history.schemas.irrigation_history import (
    IrrigationOutcome,
    IrrigationHistoryReadResponse,
    IrrigationHistoryRecord,
)
from smart_irrigation_system.server.history.repositories.irrigation_history_repository import (
    IrrigationHistoryRepository,
)
from smart_irrigation_system.server.configuration.repositories.zone_lifecycle_repository import (
    ZoneLifecycleRepository,
)
from smart_irrigation_system.server.history.schemas.irrigation_history import (
    IrrigationRecordInput,
)
from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory


class IrrigationHistoryService:
    def __init__(self, session: Session):
        self.repo = IrrigationHistoryRepository(session)
        self.zone_repo = ZoneRepository(session)

    @staticmethod
    def _compute_even_area_values(zone, record_input: IrrigationRecordInput) -> tuple[bool, float | None, float | None]:
        zone_config = zone.irrigation_configuration or {}
        is_even_area = (
            record_input.even_area_mode
            if record_input.even_area_mode is not None
            else zone.irrigation_mode == IrrigationMode.EVEN_AREA
        )

        if not is_even_area:
            return False, None, None

        target_mm = record_input.target_mm
        if target_mm is None:
            target_mm = zone_config.get("target_mm")
        if target_mm is not None:
            target_mm = float(target_mm)

        actual_mm = record_input.actual_mm
        if actual_mm is None:
            zone_area_m2 = zone_config.get("zone_area_m2")
            actual_water_amount = record_input.actual_water_amount
            if zone_area_m2 not in (None, 0) and actual_water_amount is not None:
                actual_mm = float(actual_water_amount) / float(zone_area_m2)
        elif actual_mm is not None:
            actual_mm = float(actual_mm)

        return True, target_mm, actual_mm

    @staticmethod
    def _derive_success(record_input: IrrigationRecordInput) -> bool | None:
        if record_input.success is not None:
            return record_input.success
        if record_input.outcome in {"failed", "interrupted"}:
            return False
        if record_input.outcome in {"success", "stopped", "skipped"}:
            return True
        return None

    def get_records(
        self,
        node_id: int | None = None,
        circuit_id: int | None = None,
        limit: int = 100,
        include_deleted_zones: bool = False,
        outcome: str | None = None,
    ) -> IrrigationHistoryReadResponse:
        # totals computed over all matching DB rows (ignoring limit)
        total_records = self.repo.count_records(
            node_id=node_id, circuit_id=circuit_id, include_deleted_zones=include_deleted_zones, outcome=outcome
        )

        history_records = self.repo.list_records(
            node_id=node_id, circuit_id=circuit_id, limit=limit, include_deleted_zones=include_deleted_zones, outcome=outcome
        )

        records = [
            IrrigationHistoryRecord(
                id=record.id,
                node_id=record.node_id,
                circuit_id=record.circuit_id,
                outcome=IrrigationOutcome(record.outcome),
                zone_deleted=record.zone_deleted,
                start_time=record.start_time,
                was_manual_run=record.was_manual_run,
                success=record.success if record.success is not None else record.outcome not in {"failed", "interrupted"},
                target_duration=record.target_duration,
                completed_duration=record.completed_duration,
                target_water_amount=record.target_water_amount,
                actual_water_amount=record.actual_water_amount,
                reason=record.reason,
                base_water_amount=record.base_water_amount,
                standard_conditions_solar=record.standard_conditions_solar,
                standard_conditions_rain=record.standard_conditions_rain,
                standard_conditions_temp=record.standard_conditions_temp,
                actual_solar=record.actual_solar,
                actual_rain=record.actual_rain,
                actual_temp=record.actual_temp,
                carry_over_applied=record.carry_over_applied,
                even_area_mode=record.even_area_mode,
                dynamic_interval_enabled=record.dynamic_interval_enabled,
                irrigation_volume_threshold_percent=record.irrigation_volume_threshold_percent,
                target_mm=record.target_mm,
                actual_mm=record.actual_mm,
            )
            for record in history_records
        ]
        returned_records = len(records)

        success_count = self.repo.count_successful_records(
            node_id=node_id, circuit_id=circuit_id, include_deleted_zones=include_deleted_zones, outcome=outcome
        )

        total_water = self.repo.sum_water(
            node_id=node_id, circuit_id=circuit_id, include_deleted_zones=include_deleted_zones, outcome=outcome
        )

        success_rate = float(success_count) / float(total_records) if total_records > 0 else 0.0

        return IrrigationHistoryReadResponse(
            records=records,
            total_records=total_records,
            returned_records=returned_records,
            success_rate=success_rate,
            total_water=total_water,
        )

    def upload_records(self, node_id: int, records: list[IrrigationRecordInput]) -> tuple[int, int]:
        """Upload records coming from a node.

        Returns (uploaded_count, skipped_count).
        """
        lifecycle_repo = ZoneLifecycleRepository(self.repo.session)

        if not records:
            return 0, 0

        uploaded_count = 0
        skipped_count = 0

        for record_input in records:
            # skip duplicates
            existing = self.repo.get_by_unique(node_id, record_input.circuit_id, record_input.start_time)
            if existing:
                skipped_count += 1
                continue

            zone = self.zone_repo.get(record_input.circuit_id)
            lifecycle = lifecycle_repo.get_applicable(node_id, record_input.circuit_id, record_input.start_time)
            zone_deleted = bool(lifecycle and lifecycle.deleted_at is not None)
            even_area_mode, target_mm, actual_mm = (False, None, None)
            if zone is not None:
                even_area_mode, target_mm, actual_mm = self._compute_even_area_values(zone, record_input)

            history_record = IrrigationHistory(
                node_id=node_id,
                circuit_id=record_input.circuit_id,
                zone_deleted=zone_deleted,
                start_time=record_input.start_time,
                outcome=record_input.outcome,
                success=self._derive_success(record_input),
                was_manual_run=record_input.was_manual_run,
                completed_duration=record_input.completed_duration,
                target_duration=record_input.target_duration,
                actual_water_amount=record_input.actual_water_amount,
                target_water_amount=record_input.target_water_amount,
                reason=record_input.reason,
                base_water_amount=record_input.base_water_amount,
                standard_conditions_solar=record_input.standard_conditions_solar,
                standard_conditions_rain=record_input.standard_conditions_rain,
                standard_conditions_temp=record_input.standard_conditions_temp,
                actual_solar=record_input.actual_solar,
                actual_rain=record_input.actual_rain,
                actual_temp=record_input.actual_temp,
                carry_over_applied=record_input.carry_over_applied,
                even_area_mode=even_area_mode,
                dynamic_interval_enabled=record_input.dynamic_interval_enabled,
                irrigation_volume_threshold_percent=record_input.irrigation_volume_threshold_percent,
                target_mm=target_mm,
                actual_mm=actual_mm,
            )

            self.repo.create(history_record)
            uploaded_count += 1

        # commit by caller responsibility is kept in API layer; however
        # service can commit to preserve previous behavior. We'll commit here
        # to keep existing endpoint behavior.
        self.repo.session.commit()

        return uploaded_count, skipped_count

    def delete_records(self, node_id: int | None = None, circuit_id: int | None = None) -> int:
        deleted = self.repo.delete_records(node_id=node_id, circuit_id=circuit_id)
        self.repo.session.commit()
        return deleted