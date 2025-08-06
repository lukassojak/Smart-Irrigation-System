import random
from datetime import datetime, timedelta
from smart_irrigation_system.global_conditions import GlobalConditions

INTERVAL_HOURS = 24  # Interval in hours for the collection of global conditions

class WeatherSimulator:
    """Simulates global environmental conditions for debug purposes."""
    
    def __init__(self, seed=None):
        self.rng = random.Random(seed)            # local random number generator for reproducibility
        self.current_conditions = self.update_current_conditions()

    def get_conditions_str(self) -> str:
        """Returns a string representation of the current weather conditions."""
        return (f"Temperature: {self.current_conditions.temperature:.2f} °C, "
                f"Rain: {self.current_conditions.rain_mm:.2f} mm, "
                f"Sunlight: {self.current_conditions.sunlight_hours:.2f} hours, "
                f"Timestamp: {self.current_conditions.timestamp.isoformat()}")

    def get_current_conditions(self) -> GlobalConditions:
        """Returns the current simulated weather data."""
        return self.current_conditions

    def update_current_conditions(self) -> GlobalConditions:
        """Generates simulated weather data."""
        temperature = self.rng.uniform(17, 30)    # °C in average in the last INTERVAL hours
        rain_mm = self.rng.uniform(0, 5)         # mm in the last INTERVAL hours
        sunlight_hours = self.rng.uniform(6, 14)  # number of hours of sunlight in the last INTERVAL hours
        timestamp_retrieved = datetime.now()
        self.current_conditions = GlobalConditions(
            temperature=temperature,
            rain_mm=rain_mm,
            sunlight_hours=sunlight_hours,
            timestamp=timestamp_retrieved
        )
        return self.current_conditions
    