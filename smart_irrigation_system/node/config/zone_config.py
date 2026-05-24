from dataclasses import dataclass

from smart_irrigation_system.node.config.global_config import CorrectionFactors


@dataclass
class FrequencySettings:
    dynamic_interval: bool
    min_interval_days: int
    max_interval_days: int
    carry_over_volume: bool
    irrigation_volume_threshold_percent: int


@dataclass
class ZoneConfig:
    id: int
    name: str
    relay_pin: int
    enabled: bool
    even_area_mode: bool
    base_volume_liters: float
    base_flow_lph: float
    interval_days: int
    frequency_settings: FrequencySettings
    local_correction_factors: CorrectionFactors