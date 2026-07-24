from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HistoryStatisticsQuery(BaseModel):
    node_id: Optional[int] = Field(None, description="Node ID to filter")
    circuit_id: Optional[int] = Field(None, description="Circuit ID to filter")
    include_deleted_zones: bool = Field(False, description="Whether to include deleted zones")
    outcome: Optional[str] = Field(None, description="Outcome to filter")
    range_days: Optional[int] = Field(None, description="Number of days to include, counting backwards from now")


class HistoryOverviewMetrics(BaseModel):
    total_water: float = Field(..., description="Total actual water usage in liters")
    avg_daily_water: float = Field(..., description="Average daily water usage in liters")
    irrigation_runs: int = Field(..., description="Total irrigation runs")
    success_rate: float = Field(..., description="Successful runs divided by total runs")
    avg_correction: float = Field(..., description="Average correction ratio")
    avg_duration: float = Field(..., description="Average completed duration in seconds")
    auto_runs: int = Field(..., description="Automatic irrigation runs")
    manual_runs: int = Field(..., description="Manual irrigation runs")
    interrupted_runs: int = Field(..., description="Interrupted runs")
    failed_runs: int = Field(..., description="Failed runs")
    skipped_runs: int = Field(..., description="Skipped runs")
    stopped_runs: int = Field(..., description="Stopped runs")
    first_record_at: Optional[datetime] = Field(None, description="Timestamp of the earliest matching record")
    last_record_at: Optional[datetime] = Field(None, description="Timestamp of the latest matching record")


class WaterUsageTrendPoint(BaseModel):
    date: str = Field(..., description="Bucket date in ISO YYYY-MM-DD format")
    water: float = Field(..., description="Total water usage for the bucket in liters")
    runs: int = Field(..., description="Number of irrigation runs for the bucket")


class WaterUsageTrendResponse(BaseModel):
    points: list[WaterUsageTrendPoint]
    range_days: Optional[int] = Field(None, description="Requested number of days")
    total_water: float = Field(..., description="Total actual water usage in liters for the selected range")


class OutcomeBreakdownItem(BaseModel):
    name: str = Field(..., description="Outcome label")
    value: int = Field(..., description="Number of runs for this outcome")


class OutcomeBreakdownResponse(BaseModel):
    items: list[OutcomeBreakdownItem]
    total_records: int = Field(..., description="Total matching records across the selected zones and range")


class ZoneWaterDistributionItem(BaseModel):
    circuit_id: int = Field(..., description="Circuit / zone ID")
    zone_name: Optional[str] = Field(None, description="Human readable zone name")
    water: float = Field(..., description="Total water used in liters")
    runs: int = Field(..., description="Number of irrigation runs")


class ZoneWaterDistributionResponse(BaseModel):
    items: list[ZoneWaterDistributionItem]
    total_water: float = Field(..., description="Total water across the selected zones and range")


class ZoneCorrectionTrendPoint(BaseModel):
    date: str = Field(..., description="Bucket date in ISO YYYY-MM-DD format")
    correction: float = Field(..., description="Average correction for the bucket in percentage points")
    runs: int = Field(..., description="Number of runs contributing to the bucket")


class ZoneCorrectionTrendResponse(BaseModel):
    zone_id: Optional[int] = Field(None, description="Selected circuit / zone ID")
    zone_name: Optional[str] = Field(None, description="Human readable zone name")
    points: list[ZoneCorrectionTrendPoint]
    avg_correction: float = Field(..., description="Average correction in percentage points")
