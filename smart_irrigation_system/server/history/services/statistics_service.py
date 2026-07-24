from __future__ import annotations

from typing import Optional

from sqlmodel import Session

from smart_irrigation_system.server.history.repositories.irrigation_history_repository import (
    IrrigationHistoryRepository,
)
from smart_irrigation_system.server.history.schemas.statistics import (
    HistoryOverviewMetrics,
    OutcomeBreakdownResponse,
    OutcomeBreakdownItem,
    ZoneCorrectionTrendResponse,
    ZoneCorrectionTrendPoint,
    ZoneWaterDistributionResponse,
    ZoneWaterDistributionItem,
    WaterUsageTrendResponse,
    WaterUsageTrendPoint,
)


class StatisticsService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = IrrigationHistoryRepository(session)

    def get_overview(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
    ) -> HistoryOverviewMetrics:
        total_records = self.repository.count_records(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
            range_days=range_days,
        )
        successful_records = self.repository.count_successful_records(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
            range_days=range_days,
        )
        total_water = self.repository.sum_water(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
            range_days=range_days,
        )
        avg_correction = self.repository.avg_correction(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
            range_days=range_days,
        )
        first_record_at, last_record_at = self.repository.get_record_time_bounds(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
            range_days=range_days,
        )

        avg_daily_water = 0.0
        if range_days:
            avg_daily_water = total_water / range_days if range_days > 0 else 0.0
        elif first_record_at and last_record_at:
            span_days = max((last_record_at - first_record_at).days + 1, 1)
            avg_daily_water = total_water / span_days

        success_rate = (successful_records / total_records) if total_records else 0.0
        auto_runs = total_records - self.repository.count_manual_runs(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
            range_days=range_days,
        )

        return HistoryOverviewMetrics(
            total_water=total_water,
            avg_daily_water=avg_daily_water,
            irrigation_runs=total_records,
            success_rate=success_rate,
            avg_correction=avg_correction,
            avg_duration=self._average_duration(
                node_id=node_id,
                circuit_id=circuit_id,
                include_deleted_zones=include_deleted_zones,
                outcome=outcome,
                range_days=range_days,
            ),
            auto_runs=auto_runs,
            manual_runs=self.repository.count_manual_runs(
                node_id=node_id,
                circuit_id=circuit_id,
                include_deleted_zones=include_deleted_zones,
                outcome=outcome,
                range_days=range_days,
            ),
            interrupted_runs=self.repository.count_outcome_records(
                "interrupted",
                node_id=node_id,
                circuit_id=circuit_id,
                include_deleted_zones=include_deleted_zones,
                outcome=outcome,
                range_days=range_days,
            ),
            failed_runs=self.repository.count_outcome_records(
                "failed",
                node_id=node_id,
                circuit_id=circuit_id,
                include_deleted_zones=include_deleted_zones,
                outcome=outcome,
                range_days=range_days,
            ),
            skipped_runs=self.repository.count_outcome_records(
                "skipped",
                node_id=node_id,
                circuit_id=circuit_id,
                include_deleted_zones=include_deleted_zones,
                outcome=outcome,
                range_days=range_days,
            ),
            stopped_runs=self.repository.count_outcome_records(
                "stopped",
                node_id=node_id,
                circuit_id=circuit_id,
                include_deleted_zones=include_deleted_zones,
                outcome=outcome,
                range_days=range_days,
            ),
            first_record_at=first_record_at,
            last_record_at=last_record_at,
        )

    def get_water_usage_trend(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
    ) -> WaterUsageTrendResponse:
        points = self.repository.get_daily_water_trend(
            node_id=node_id,
            circuit_id=circuit_id,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
            range_days=range_days,
        )
        total_water = sum(point["water"] for point in points)
        return WaterUsageTrendResponse(
            points=[WaterUsageTrendPoint(**point) for point in points],
            range_days=range_days,
            total_water=total_water,
        )

    def get_outcome_breakdown(
        self,
        node_id: Optional[int] = None,
        circuit_ids: Optional[list[int]] = None,
        include_deleted_zones: bool = False,
        range_days: Optional[int] = None,
    ) -> OutcomeBreakdownResponse:
        items = self.repository.get_outcome_breakdown(
            node_id=node_id,
            circuit_ids=circuit_ids,
            include_deleted_zones=include_deleted_zones,
            range_days=range_days,
        )
        total_records = sum(item["value"] for item in items)
        return OutcomeBreakdownResponse(
            items=[OutcomeBreakdownItem(**item) for item in items],
            total_records=total_records,
        )

    def get_zone_water_distribution(
        self,
        node_id: Optional[int] = None,
        circuit_ids: Optional[list[int]] = None,
        include_deleted_zones: bool = False,
        range_days: Optional[int] = None,
    ) -> ZoneWaterDistributionResponse:
        items = self.repository.get_zone_water_distribution(
            node_id=node_id,
            circuit_ids=circuit_ids,
            include_deleted_zones=include_deleted_zones,
            range_days=range_days,
        )
        total_water = sum(item["water"] for item in items)
        return ZoneWaterDistributionResponse(
            items=[ZoneWaterDistributionItem(**item) for item in items],
            total_water=total_water,
        )

    def get_zone_correction_trend(
        self,
        circuit_id: Optional[int] = None,
        node_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        range_days: Optional[int] = None,
    ) -> ZoneCorrectionTrendResponse:
        points = self.repository.get_zone_correction_trend(
            circuit_id=circuit_id,
            node_id=node_id,
            include_deleted_zones=include_deleted_zones,
            range_days=range_days,
        )
        avg_correction = 0.0
        if points:
            avg_correction = sum(point["correction"] for point in points) / len(points)

        zone_name = None
        if circuit_id is not None:
            zone_name = self.repository.get_zone_name(circuit_id)

        return ZoneCorrectionTrendResponse(
            zone_id=circuit_id,
            zone_name=zone_name,
            points=[ZoneCorrectionTrendPoint(**point) for point in points],
            avg_correction=avg_correction,
        )

    def _average_duration(
        self,
        node_id: Optional[int] = None,
        circuit_id: Optional[int] = None,
        include_deleted_zones: bool = False,
        outcome: Optional[str] = None,
        range_days: Optional[int] = None,
    ) -> float:
        records = self.repository.list_records(
            node_id=node_id,
            circuit_id=circuit_id,
            limit=10000,
            include_deleted_zones=include_deleted_zones,
            outcome=outcome,
            range_days=range_days,
        )
        durations = [record.get("completed_duration") for record in records if record.get("completed_duration") is not None]
        if not durations:
            return 0.0
        return float(sum(durations) / len(durations))
