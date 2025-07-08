import random
from datetime import datetime, timedelta
from smart_irrigation_system.global_conditions import GlobalConditions

INTERVAL_HOURS = 24  # Interval in hours for the collection of global conditions

class WeatherSimulator:
    """Simulates global environmental conditions for debug purposes."""
    
    def __init__(self, seed=None):
        self.rng = random.Random(seed)            # local random number generator for reproducibility

    def get_current_conditions(self) -> GlobalConditions:
        """Generates simulated weather data."""
        temperature = self.rng.uniform(10, 40)    # °C in average in the last INTERVAL hours
        rain_mm = self.rng.uniform(0, 30)         # mm in the last INTERVAL hours
        sunlight_hours = self.rng.uniform(0, 16)  # number of hours of sunlight in the last INTERVAL hours
        timestamp_retrieved = datetime.now()
        return GlobalConditions(
            temperature=temperature,
            rain_mm=rain_mm,
            sunlight_hours=sunlight_hours,
            timestamp=timestamp_retrieved
        )
    