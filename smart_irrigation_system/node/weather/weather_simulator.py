import random
from datetime import datetime, timedelta
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions
from smart_irrigation_system.node.utils.logger import get_logger


INTERVAL_HOURS = 24  # Interval in hours for the collection of global conditions
INTERVAL_DAYS_LIMIT = 7  # Maximum number of days for interval_days parameter


class WeatherSimulator:
    """Simulates global environmental conditions for debug purposes."""

    def __init__(self, seed=None):
        self.logger = get_logger("WeatherSimulator")
        self.rng = random.Random(seed)  # Local random number generator for reproducibility
        self.current_conditions = self.update_current_conditions()
        self._last_cache_update = datetime.min
        self._cached_temperatures = {}
        self._cached_rainfall = {}
        self._cached_solar = {}
        self._cached_real_time_rainfall = None
        self.logger.info("WeatherSimulator initialized.")

    @property
    def last_cache_update(self) -> datetime:
        """Returns the timestamp of the last cache update."""
        return self._last_cache_update

    @property
    def cached_temperatures(self) -> dict[datetime, float]:
        """Returns the cached temperatures."""
        return self._cached_temperatures

    @property
    def cached_rainfall(self) -> dict[datetime, float]:
        """Returns the cached rainfall data."""
        return self._cached_rainfall

    @property
    def cached_real_time_rainfall(self) -> float | None:
        """Returns the cached real-time rainfall."""
        return self._cached_real_time_rainfall

    @property
    def cached_solar(self) -> dict[datetime, float]:
        """Returns the cached solar data."""
        return self._cached_solar

    @cached_temperatures.setter
    def cached_temperatures(self, temperatures: dict[datetime, float]) -> None:
        """Sets the cached temperatures and updates the last cache update timestamp."""
        self._cached_temperatures = temperatures
        self._last_cache_update = datetime.now()
        self.logger.debug("Cached temperatures updated.")

    @cached_rainfall.setter
    def cached_rainfall(self, rainfall: dict[datetime, float]) -> None:
        """Sets the cached rainfall data and updates the last cache update timestamp."""
        self._cached_rainfall = rainfall
        self._last_cache_update = datetime.now()
        self.logger.debug("Cached rainfall updated.")

    @cached_solar.setter
    def cached_solar(self, solar: dict[datetime, float]) -> None:
        """Sets the cached solar data and updates the last cache update timestamp."""
        self._cached_solar = solar
        self._last_cache_update = datetime.now()
        self.logger.debug("Cached solar data updated.")

    @cached_real_time_rainfall.setter
    def cached_real_time_rainfall(self, rainfall: float) -> None:
        """Sets the cached real-time rainfall and updates the last cache update timestamp."""
        self._cached_real_time_rainfall = rainfall
        self._last_cache_update = datetime.now()
        self.logger.debug("Cached real-time rainfall updated.")

    def _data_expired(self) -> bool:
        """Checks if the cached data has expired based on the INTERVAL_HOURS."""
        return self.last_cache_update + timedelta(hours=INTERVAL_HOURS) < datetime.now()

    def get_current_conditions(self, interval_days: int = None, force_update: bool = False) -> GlobalConditions:
        """Returns the current simulated weather data."""
        interval_days = interval_days if interval_days is not None else INTERVAL_DAYS_LIMIT
        if interval_days > INTERVAL_DAYS_LIMIT:
            self.logger.warning(f"Interval days {interval_days} exceeds limit of {INTERVAL_DAYS_LIMIT}. Using limit value.")
            interval_days = INTERVAL_DAYS_LIMIT

        if self._data_expired() or force_update:
            self.logger.debug("Simulated weather data expired or force update requested. Generating new data.")
            self.update_current_conditions()
        else:
            self.logger.debug("Using cached simulated weather data.")

        return self.current_conditions

    def get_conditions_str(self) -> str:
        """Returns a string representation of the current weather conditions."""
        if self.current_conditions is None:
            return "No current weather conditions available."
        solar_watts = self.current_conditions.solar_total * 1000  # Convert kWh/m² to W/m²
        return (f"Temperature: {self.current_conditions.temperature:.2f} °C, "
                f"Rain: {self.current_conditions.rain_mm:.2f} mm, "
                f"Solar: {solar_watts:.2f} W/m², "
                f"Timestamp: {self.current_conditions.timestamp.isoformat()}")

    def update_current_conditions(self) -> GlobalConditions:
        """Generates simulated weather data."""
        temperature = self.rng.uniform(13, 28)  # °C in average in the last INTERVAL hours
        rain_mm = self.rng.uniform(0, 7)  # mm in the last INTERVAL hours
        sunlight_hours = self.rng.uniform(4, 8)  # number of hours of sunlight in the last INTERVAL hours
        timestamp_retrieved = datetime.now()

        # Update cached data
        self.cached_temperatures = {timestamp_retrieved: temperature}
        self.cached_rainfall = {timestamp_retrieved: rain_mm}
        self.cached_solar = {timestamp_retrieved: sunlight_hours}
        self.cached_real_time_rainfall = rain_mm

        self.current_conditions = GlobalConditions(
            temperature=temperature,
            rain_mm=rain_mm,
            solar_total=sunlight_hours,
            timestamp=timestamp_retrieved
        )
        return self.current_conditions

    def _get_avg_temperature(self, interval_days: int) -> float:
        """Fetches the average temperature over the specified interval."""
        return self.current_conditions.temperature

    def _get_total_rainfall(self, interval_days: int) -> float:
        """Fetches the total rainfall over the specified interval."""
        return self.current_conditions.rain_mm

    def _get_total_solar(self, interval_days: int) -> float:
        """Fetches the total solar radiation over the specified interval."""
        return self.current_conditions.solar_total