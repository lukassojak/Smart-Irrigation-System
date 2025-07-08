from dataclasses import dataclass
from datetime import datetime

INTERVAL = 24  # Interval in hours for the collection of global conditions


@dataclass
class GlobalConditions:
    """Holds the global environmental conditions"""
    temperature: float      # °C
    rain_mm: float          # mm of rain in the last INTERVAL hours
    sunlight_hours: float   # number of hours of sunlight in the last INTERVAL hours
    timestamp: datetime     # Timestamp of the last update