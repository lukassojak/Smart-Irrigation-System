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
from typing import Optional, List, Tuple


class IrrigationHistoryService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = IrrigationHistoryRepository(session)

    def upload_records(self, node_id: int, records: List[dict]) -> Tuple[int, int]:
        return self.repository.upload_records(node_id=node_id, records=records)

    def get_records(self, node_id: Optional[int] = None, circuit_id: Optional[int] = None, limit: int = 100, include_deleted_zones: bool = False, outcome: Optional[str] = None) -> IrrigationHistoryReadResponse:
        raw_records = self.repository.list_records(
            node_id=node_id,
            circuit_id=circuit_id,
            limit=limit,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
        )
        records = [self._enrich_record(rec) for rec in raw_records]
        total_records = self.repository.count_records(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
        )
        returned_records = len(records)
        successful_records = self.repository.count_successful_records(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
        )
        success_rate = (successful_records / total_records) if total_records else 0.0
        total_water = self.repository.sum_water(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
        )
        avg_correction = self.repository.avg_correction(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
        )
        return IrrigationHistoryReadResponse(
            records=records,
            total_records=total_records,
            returned_records=returned_records,
            success_rate=success_rate,
            total_water=total_water,
            avg_correction=avg_correction,
        )

    def get_record(self, node_id: int, circuit_id: int, start_time: Optional[object] = None) -> Optional[IrrigationHistoryRecord]:
        rec = self.repository.get_by_unique(node_id=node_id, circuit_id=circuit_id, start_time=start_time)
        return self._enrich_record(rec)

    def get_record_by_id(self, record_id: int) -> Optional[IrrigationHistoryRecord]:
        rec = self.repository.get_by_id(record_id=record_id)
        return self._enrich_record(rec)

    def delete_record(self, node_id: int, circuit_id: int, start_time: Optional[object] = None) -> int:
        return self.repository.delete_record(node_id=node_id, circuit_id=circuit_id, start_time=start_time)

    def delete_record_by_id(self, record_id: int) -> int:
        return self.repository.delete_record_by_id(record_id=record_id)

    def delete_records(self, node_id: Optional[int] = None, circuit_id: Optional[int] = None) -> int:
        return self.repository.delete_records(node_id=node_id, circuit_id=circuit_id)

    def _enrich_record(self, rec: Optional[dict]) -> Optional[IrrigationHistoryRecord]:
        if not rec:
            return None

        zone_name = None
        if rec.get("circuit_id") is not None:
            zone_name = self.repository.get_zone_name(circuit_id=rec["circuit_id"])

        if isinstance(rec, IrrigationHistoryRecord):
            rec.zone_name = zone_name
            return rec

        payload = dict(rec)
        payload["zone_name"] = zone_name
        return IrrigationHistoryRecord(**payload)