from datetime import datetime, timedelta
import requests, json
from typing import Optional

from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.global_conditions import GlobalConditions
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.secrets import get_secret
from smart_irrigation_system.ecowitt_api import (
    temperature_api_call,
    rainfall_api_call_history,
    solar_api_call_history,
    all_api_call_real_time,
    test_api_secrets_valid
)
from smart_irrigation_system.weather_data_processor import (
    calculate_avg_temperature,
    calculate_total_rainfall,
    calculate_total_solar
)

from smart_irrigation_system.weather_config import (
    TEMPERATURE_TIME_RESOLUTION,
    RAINFALL_TIME_RESOLUTION,
    MIN_TEMPERATURE_COUNT,
    MAX_DATA_AGE,
    CELSIUS
)

INTERVAL_DAYS_LIMIT = 7 # Maximum number of days for interval_days parameter (API limitation)

# Constants for testing purposes
TEMP_TEST_START_DATE = datetime(2025, 7, 30, 18, 0, 0)
TEMP_TEST_END_DATE = datetime(2025, 8, 2, 20, 10, 0)

class RecentWeatherFetcher:
    def __init__(self, global_config: GlobalConfig, max_interval_days: int):
        self.logger = get_logger("RecentWeatherFetcher")
        self.global_config: GlobalConfig = global_config
        self.max_interval_days: int = max_interval_days if max_interval_days <= INTERVAL_DAYS_LIMIT else INTERVAL_DAYS_LIMIT
        self.current_conditions: GlobalConditions = None
        self._use_standard_conditions: bool = False
        self.try_reconnect: bool = False
        self.connecting: bool = False

        # Check if the API is enabled
        if not self.global_config.weather_api.api_enabled:
            self.logger.warning("Weather API is not enabled. Please check your configuration. RecentWeatherFetcher will use standard conditions as fallback.")
            self._use_standard_conditions = True

        # Validate API secrets
        try:
            self.connecting = True
            if not test_api_secrets_valid(self, global_config):
                self.logger.error("Invalid API secrets. Please check your configuration. RecentWeatherFetcher will use standard conditions as fallback.")
                self._use_standard_conditions = True
            else:
                self.logger.info("API secrets validated successfully.")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error while validating API secrets: {e}.")
            self.logger.warning("Internet connection issue. RecentWeatherFetcher will try to connect later.")
            self.try_reconnect = True
        except Exception as e:
            self.logger.error(f"Error while validating API secrets: {e}. RecentWeatherFetcher will use standard conditions as fallback.")
            self._use_standard_conditions = True
        finally:
            self.connecting = False

        # Initialize current conditions with standard conditions for fallback
        self._standard_conditions = GlobalConditions(
                temperature=self.global_config.standard_conditions.temperature_celsius,
                rain_mm=self.global_config.standard_conditions.rain_mm,
                solar_total=self.global_config.standard_conditions.solar_total,
                timestamp=datetime.now()
            )

        # Cache for fetched weather data
        self._last_cache_update: datetime = datetime.min
        self._cached_temperatures: dict[datetime, float] = {}
        self._cached_rainfall: dict[datetime, float] = {}       
        self._cached_solar: dict[datetime, float] = {}
        # Real-time rainfall data
        self._cached_real_time_rainfall: float | None = None
        self.get_current_conditions(force_update=True)

        self.logger.info("RecentWeatherFetcher initialized.")

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
        self.logger.debug(f"Cached temperatures updated.")
    
    @cached_rainfall.setter
    def cached_rainfall(self, rainfall: dict[datetime, float]) -> None:
        """Sets the cached rainfall data and updates the last cache update timestamp."""
        self._cached_rainfall = rainfall
        self._last_cache_update = datetime.now()
        self.logger.debug(f"Cached rainfall updated.")

    @cached_solar.setter
    def cached_solar(self, solar: dict[datetime, float]) -> None:
        """Sets the cached solar data and updates the last cache update timestamp."""
        self._cached_solar = solar
        self._last_cache_update = datetime.now()
        self.logger.debug(f"Cached solar data updated.")

    @cached_real_time_rainfall.setter
    def cached_real_time_rainfall(self, rainfall: float) -> None:
        """Sets the cached real-time rainfall and updates the last cache update timestamp."""
        self._cached_real_time_rainfall = rainfall
        self._last_cache_update = datetime.now()
        self.logger.debug(f"Cached real-time rainfall updated.")



    def _data_expired(self) -> bool:
        """Checks if the cached data has expired based on the MAX_DATA_AGE."""
        if self.last_cache_update is None:
            return True
        return self.last_cache_update + timedelta(seconds=MAX_DATA_AGE) < datetime.now()


    def get_current_conditions(self, interval_days: Optional[int] = None, force_update: bool = False) -> GlobalConditions:
        """Updates the current weather conditions by fetching data from the API."""
        interval_days = interval_days if interval_days is not None else self.max_interval_days
        if interval_days > INTERVAL_DAYS_LIMIT:
            self.logger.warning(f"Interval days {interval_days} exceeds limit of {INTERVAL_DAYS_LIMIT}. Using limit value.")
            interval_days = INTERVAL_DAYS_LIMIT

        if self._use_standard_conditions:
            self.logger.error("Cannot update current conditions. Using standard conditions as fallback.")
            return self._standard_conditions

        if self.try_reconnect:
            force_update = True
            self.logger.info("Trying to reconnect to the API...")
        # For now, fetch temperatures and rainfall data only if the data is expired or not cached
        if self._data_expired() or not self.cached_temperatures or force_update:
            try:
                self.connecting = True
                self._update_cache()
                self.try_reconnect = False
                self.logger.debug("Weather data cache updated successfully.")
            except Exception as e:
                self.try_reconnect = True
                self.logger.warning("Failed to update weather data cache, using standard conditions as fallback.")
                return self._standard_conditions
            finally:
                self.connecting = False
        else:
            self.logger.debug("Using cached current conditions.")

        avg_temperature = self._get_avg_temperature(interval_days)
        total_rainfall = self._get_total_rainfall(interval_days)
        solar_total = self._get_total_solar(interval_days)
        timestamp_retrieved = self.last_cache_update
        self.current_conditions = GlobalConditions(
            temperature=avg_temperature,
            rain_mm=total_rainfall,
            solar_total=solar_total,
            timestamp=timestamp_retrieved
        )
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

    
    def _get_avg_temperature(self, interval_days: int) -> float:
        """Fetches the average temperature over the specified interval."""
        if self._data_expired() or not self.cached_temperatures:
            self._cache_temperatures()
        
        # maybe can be replaced just with datetime.now() - timedelta(days=interval_days)
        start_date_timestamp = self._get_closest_timestamp_in_dict(
            datetime.now() - timedelta(days=interval_days), self._cached_temperatures
        )
        if start_date_timestamp is None:
            self.logger.warning("No cached temperature data available for the specified interval, using standard conditions.")
            return self.global_config.standard_conditions.temperature_celsius
        
        relevant_temperatures = [
            temp for timestamp, temp in self._cached_temperatures.items()
            if timestamp >= start_date_timestamp
        ]

        if len(relevant_temperatures) < MIN_TEMPERATURE_COUNT:
            self.logger.warning(f"Not enough temperature data points ({len(relevant_temperatures)}) to calculate average. Using standard conditions.")
            return self.global_config.standard_conditions.temperature_celsius
        
        return sum(relevant_temperatures) / len(relevant_temperatures)

    
    def _get_total_rainfall(self, interval_days: int) -> float:
        """Fetches the total rainfall over the specified interval."""
        if self._data_expired() or not self._cached_rainfall:
            self._cache_rainfall()

        start_date_timestamp = self._get_closest_timestamp_in_dict(
            datetime.now() - timedelta(days=interval_days), self._cached_rainfall
        )
        if start_date_timestamp is None:
            self.logger.warning("No cached rainfall data available for the specified interval, using standard conditions.")
            return self.global_config.standard_conditions.rain_mm
        
        start_date_rainfall = self._cached_rainfall.get(start_date_timestamp)
        real_time_rainfall = self.cached_real_time_rainfall
        
        if real_time_rainfall is None:
            self.logger.warning("No real-time rainfall data available, using cached rainfall data.")
            current_timestamp = self._get_closest_timestamp_in_dict(datetime.now(), self._cached_rainfall)
            if current_timestamp is None:
                self.logger.warning("No current timestamp found in cached rainfall data, using standard conditions.")
                return self.global_config.standard_conditions.rain_mm
            real_time_rainfall = self._cached_rainfall.get(current_timestamp)
        
        return real_time_rainfall - start_date_rainfall
    
    def _get_total_solar(self, interval_days: int) -> float:
        """Fetches the total solar radiation over the specified interval. Returns the sum of solar radiation values in kWh/m²."""
        if self._data_expired() or not self.cached_solar:
            self._cache_solar()

        start_date_timestamp = self._get_closest_timestamp_in_dict(
            datetime.now() - timedelta(days=interval_days), self.cached_solar
        )
        if start_date_timestamp is None:
            self.logger.warning("No cached solar data available for the specified interval, using standard conditions.")
            return self.global_config.standard_conditions.solar_total
        
        relevant_solar_data = [
            solar for timestamp, solar in self.cached_solar.items()
            if timestamp >= start_date_timestamp
        ]

        if not relevant_solar_data:
            self.logger.warning("No relevant solar data found for the specified interval, using standard conditions.")
            return self.global_config.standard_conditions.solar_total
        
        # Return the sum of solar radiation values and convert to kWh/m²
        total_solar = (sum(relevant_solar_data) / interval_days) / 1000  # Convert W/m² to kWh/m²
        return total_solar



    # Cache management methods

    def _update_cache(self) -> None:
        """Updates the cache for temperatures and rainfall data."""
        self.logger.debug("Updating cache for temperatures, rainfall, solar, and real-time weather data.")
        if self._use_standard_conditions:
            self.logger.error("Cannot update cache. Using standard conditions as fallback.")
            return
        
        self._cache_temperatures()
        self._cache_rainfall()
        self._cache_solar()
        self._cache_real_time_weather()
        self.logger.debug("Cache updated successfully.")
    
    def _cache_temperatures(self) -> None:
        """Fetches the temperatures for the last <max_interval_days> days and caches them as a dictionary."""
        temperatures: dict[str, str] = temperature_api_call(
            self,
            start_date=datetime.now() - timedelta(days=self.max_interval_days),
            end_date=datetime.now()
        )
        self.logger.debug(f"Fetched temperatures data: {temperatures}")

        # convert the temperatures to a dictionary with datetime keys and float values
        self.cached_temperatures = {
            datetime.fromtimestamp(int(timestamp)): float(temp)
            for timestamp, temp in temperatures.items()
            if temp.replace('.', '', 1).replace('-', '', 1).isdigit()
        }

        # log the difference in the number of temperatures fetched
        self.logger.debug(f"Cached {len(self._cached_temperatures)} from {len(temperatures)} temperatures fetched from API.")

        
    def _cache_rainfall(self) -> None:
        """Fetches the rainfall data for the last <max_interval_days> days and caches it as a dictionary."""
        rainfall_data: dict[str, str] = rainfall_api_call_history(
            self,
            start_date=datetime.now() - timedelta(days=self.max_interval_days),
            end_date=datetime.now()
        )
        # sort the rainfall data by timestamp (ecowitt API returns data in reverse chronological order when the date range crosses from one month to another)
        rainfall_data_sorted: dict[str, str] = dict(sorted(rainfall_data.items()))
        self.logger.debug(f"Fetched rainfall data: {rainfall_data_sorted}")

        # convert the rainfall data to a dictionary with datetime keys and float values
        self.cached_rainfall = {
            datetime.fromtimestamp(int(timestamp)): float(rain)
            for timestamp, rain in rainfall_data_sorted.items()
            if rain.replace('.', '', 1).replace('-', '', 1).isdigit()
        }

        # log the difference in the number of rainfall entries fetched
        self.logger.debug(f"Cached {len(self._cached_rainfall)} from {len(rainfall_data)} rainfall entries fetched from API.")
    
    def _cache_solar(self) -> None:
        """Fetches the solar data for the last <max_interval_days> days and caches it as a dictionary."""
        solar_data: dict[str, str] = solar_api_call_history(
            self,
            start_date=datetime.now() - timedelta(days=self.max_interval_days),
            end_date=datetime.now()
        )
        self.logger.debug(f"Fetched solar data: {solar_data}")

        # convert the solar data to a dictionary with datetime keys and float values
        self.cached_solar = {
            datetime.fromtimestamp(int(timestamp)): float(solar)
            for timestamp, solar in solar_data.items()
            if solar.replace('.', '', 1).replace('-', '', 1).isdigit()
        }

        # log the difference in the number of solar entries fetched
        self.logger.debug(f"Cached {len(self._cached_solar)} from {len(solar_data)} solar entries fetched from API.")
    
    def _cache_real_time_weather(self) -> None:
        """Fetches the real-time weather data and caches it."""
        real_time_data: dict[str, str] = all_api_call_real_time(self)
        # Add the real-time temperature to the cached temperatures dictionary
        if real_time_data and 'temperature' in real_time_data:
            temperature = float(real_time_data['temperature'])
            current_cached_temperatures = self.cached_temperatures
            current_cached_temperatures[datetime.now()] = temperature
            self.cached_temperatures = current_cached_temperatures
            self.logger.debug(f"Cached real-time temperature: {temperature} °C")
        else:
            self.logger.warning("No real-time temperature data available.")

        # Add the real-time rainfall to the _cached_real_time_rainfall
        if real_time_data and 'rainfall' in real_time_data:
            rainfall = float(real_time_data['rainfall'])
            self._cached_real_time_rainfall = rainfall
            self.logger.debug(f"Cached real-time rainfall: {rainfall} mm")
        else:
            self.logger.warning("No real-time rainfall data available.")

        


    # other helper methods

    def _get_closest_timestamp_in_dict(self, start_date: datetime, dict_data: dict[datetime, float]) -> datetime:
        """Returns the closest timestamp in the dictionary to the start date."""
        if not dict_data:
            self.logger.warning("The dictionary is empty. Cannot find closest timestamp.")
            return None
        closest_timestamp = min(dict_data.keys(), key=lambda x: abs(x - start_date))
        return closest_timestamp

        

        