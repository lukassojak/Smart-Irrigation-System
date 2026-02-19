from pydantic import BaseModel
from enum import Enum


# ---- Enums ----

class SimpleFallbackStrategyType(str, Enum):
    USE_BASE_VOLUME = "use_base_volume"
    USE_HALF_BASE_VOLUME = "use_half_base_volume"
    SKIP_IRRIGATION = "skip_irrigation"

class FullFallbackStrategyType(str, Enum):
    USE_CACHED_DATA = "use_cached_data"
    USE_BASE_VOLUME = "use_base_volume"
    USE_HALF_BASE_VOLUME = "use_half_base_volume"
    SKIP_IRRIGATION = "skip_irrigation"


# ---- Irrigation Schemas ----

class IrrigationLimits(BaseModel):
    min_percent: int
    max_percent: int
    main_valve_max_flow: int | None

class Automation(BaseModel):
    enabled: bool
    scheduled_hour: int
    scheduled_minute: int
    weather_cache_interval_minutes: int
    weather_cache_expiry_hours: int

class LocalCorrectionFactors(BaseModel):
    solar: float
    rain: float
    temperature: float

class FrequencySettings(BaseModel):
    dynamic_interval: bool
    min_interval_days: int
    max_interval_days: int
    carry_over_volume: bool
    irrigation_volume_threshold_percent: int

class BatchStrategy(BaseModel):
    concurrent_irrigation: bool
    flow_control: bool
    max_concurrent_zones: int | None
    max_total_irrigation_time_minutes: int | None

class FallbackStrategy(BaseModel):
    on_fresh_weather_data_unavailable: FullFallbackStrategyType
    on_expired_weather_data: FullFallbackStrategyType   # data older than cache expiry, but still available
    on_missing_weather_data: SimpleFallbackStrategyType

class IrrigationConfigurationEvenArea(BaseModel):
    zone_area_m2: float
    target_mm: float

class IrrigationConfigurationPerPlant(BaseModel):
    base_target_volume_liters: float