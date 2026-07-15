from sqlmodel import Session

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
                target_duration=record.target_duration,
                completed_duration=record.completed_duration,
                target_water_amount=record.target_water_amount,
                actual_water_amount=record.actual_water_amount,
                reason=record.reason,
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

            lifecycle = lifecycle_repo.get_applicable(node_id, record_input.circuit_id, record_input.start_time)
            zone_deleted = bool(lifecycle and lifecycle.deleted_at is not None)

            history_record = IrrigationHistory(
                node_id=node_id,
                circuit_id=record_input.circuit_id,
                zone_deleted=zone_deleted,
                start_time=record_input.start_time,
                outcome=record_input.outcome,
                completed_duration=record_input.completed_duration,
                target_duration=record_input.target_duration,
                actual_water_amount=record_input.actual_water_amount,
                target_water_amount=record_input.target_water_amount,
                reason=record_input.reason,
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