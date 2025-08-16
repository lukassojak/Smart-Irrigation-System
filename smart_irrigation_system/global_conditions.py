from dataclasses import dataclass
from datetime import datetime

INTERVAL = 24  # Interval in hours for the collection of global conditions


@dataclass
class GlobalConditions:
    """Holds the global environmental conditions. Does not validate the data or types."""
    temperature: float      # °C
    rain_mm: float          # mm of rain in the circuit 
    solar_total: float      # Total solar radiation in the last INTERVAL hours (in W/m²)
    timestamp: datetime     # Timestamp of the last update