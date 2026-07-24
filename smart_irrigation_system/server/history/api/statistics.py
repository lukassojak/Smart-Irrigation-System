"""Statistics API router for irrigation history analytics."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from smart_irrigation_system.server.db.session import get_session
from smart_irrigation_system.server.history.schemas.statistics import (
	HistoryOverviewMetrics,
	OutcomeBreakdownResponse,
	ZoneCorrectionTrendResponse,
	ZoneWaterDistributionResponse,
	WaterUsageTrendResponse,
)
from smart_irrigation_system.server.history.services.statistics_service import StatisticsService


router = APIRouter()


@router.get(
	"/overview",
	summary="Get irrigation statistics overview",
	response_model=HistoryOverviewMetrics,
)
def get_overview(
	node_id: Optional[int] = None,
	circuit_id: Optional[int] = None,
	include_deleted_zones: bool = False,
	outcome: Optional[str] = None,
	range_days: Optional[int] = Query(default=30, ge=1, le=3650),
	session: Session = Depends(get_session),
) -> HistoryOverviewMetrics:
	try:
		service = StatisticsService(session)
		return service.get_overview(
			node_id=node_id,
			circuit_id=circuit_id,
			include_deleted_zones=include_deleted_zones,
			outcome=outcome,
			range_days=range_days,
		)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics overview: {str(e)}")


@router.get(
	"/water-usage-trend",
	summary="Get irrigation water usage trend",
	response_model=WaterUsageTrendResponse,
)
def get_water_usage_trend(
	node_id: Optional[int] = None,
	circuit_id: Optional[int] = None,
	include_deleted_zones: bool = False,
	outcome: Optional[str] = None,
	range_days: Optional[int] = Query(default=7, ge=1, le=3650),
	session: Session = Depends(get_session),
) -> WaterUsageTrendResponse:
	try:
		service = StatisticsService(session)
		return service.get_water_usage_trend(
			node_id=node_id,
			circuit_id=circuit_id,
			include_deleted_zones=include_deleted_zones,
			outcome=outcome,
			range_days=range_days,
		)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to retrieve water usage trend: {str(e)}")


def _normalize_circuit_ids(circuit_ids: Optional[list[int]] = None, circuit_id: Optional[int] = None) -> Optional[list[int]]:
	normalized_ids = []
	if circuit_ids:
		normalized_ids.extend(circuit_ids)
	if circuit_id is not None:
		normalized_ids.append(circuit_id)
	if not normalized_ids:
		return None
	return list(dict.fromkeys(normalized_ids))


@router.get(
	"/outcome-breakdown",
	summary="Get irrigation outcome breakdown",
	response_model=OutcomeBreakdownResponse,
)
def get_outcome_breakdown(
	node_id: Optional[int] = None,
	circuit_id: Optional[int] = None,
	circuit_ids: Optional[list[int]] = Query(default=None),
	include_deleted_zones: bool = False,
	range_days: Optional[int] = Query(default=30, ge=1, le=3650),
	session: Session = Depends(get_session),
) -> OutcomeBreakdownResponse:
	try:
		service = StatisticsService(session)
		return service.get_outcome_breakdown(
			node_id=node_id,
			circuit_ids=_normalize_circuit_ids(circuit_ids=circuit_ids, circuit_id=circuit_id),
			include_deleted_zones=include_deleted_zones,
			range_days=range_days,
		)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to retrieve outcome breakdown: {str(e)}")


@router.get(
	"/zone-correction-trend",
	summary="Get zone correction trend",
	response_model=ZoneCorrectionTrendResponse,
)
def get_zone_correction_trend(
	node_id: Optional[int] = None,
	circuit_id: Optional[int] = None,
	include_deleted_zones: bool = False,
	range_days: Optional[int] = Query(default=30, ge=1, le=3650),
	session: Session = Depends(get_session),
) -> ZoneCorrectionTrendResponse:
	try:
		service = StatisticsService(session)
		return service.get_zone_correction_trend(
			circuit_id=circuit_id,
			node_id=node_id,
			include_deleted_zones=include_deleted_zones,
			range_days=range_days,
		)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to retrieve zone correction trend: {str(e)}")


@router.get(
	"/zone-water-distribution",
	summary="Get zone water distribution",
	response_model=ZoneWaterDistributionResponse,
)
def get_zone_water_distribution(
	node_id: Optional[int] = None,
	circuit_id: Optional[int] = None,
	circuit_ids: Optional[list[int]] = Query(default=None),
	include_deleted_zones: bool = False,
	range_days: Optional[int] = Query(default=30, ge=1, le=3650),
	session: Session = Depends(get_session),
) -> ZoneWaterDistributionResponse:
	try:
		service = StatisticsService(session)
		return service.get_zone_water_distribution(
			node_id=node_id,
			circuit_ids=_normalize_circuit_ids(circuit_ids=circuit_ids, circuit_id=circuit_id),
			include_deleted_zones=include_deleted_zones,
			range_days=range_days,
		)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to retrieve zone water distribution: {str(e)}")

