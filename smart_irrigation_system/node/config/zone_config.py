from dataclasses import dataclass
from typing import Optional


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
    frequency_settings: dict | None = None
    local_correction_factors: dict | None = None
