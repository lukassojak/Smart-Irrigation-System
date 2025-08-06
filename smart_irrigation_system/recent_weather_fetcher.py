from datetime import datetime, timedelta
import requests, json

from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.global_conditions import GlobalConditions
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.secrets import get_secret

TEMPERATURE_TIME_RESOLUTION = 30 # in minutes, supported values: 5, 30, 240, 1440
MAX_DATA_AGE = 30 * 60 # 30 minutes in seconds; maximum age of data to consider valid, for older data a new API call is made

CELSIUS = "1"
FAHRENHEIT = "2"

class RecentWeatherFetcher:
    def __init__(self, global_config: GlobalConfig, max_interval_days: int):
        if not global_config.weather_api.api_enabled:
            # If the weather API is not enabled, do not initialize the fetcher
            raise ValueError("Weather API is not enabled in the global configuration.")

        self.logger = get_logger("RecentWeatherFetcher")
        self.global_config: GlobalConfig = global_config
        self.max_interval_days: int = max_interval_days     # Maximum interval in days between irrigation events
        self.current_conditions: GlobalConditions = None
        self.logger.info("RecentWeatherFetcher initialized with weather API enabled.")

        self._last_cache_update: datetime = datetime.min
        self._cached_temperatures: list[float] = []

    @property
    def last_cache_update(self) -> datetime:
        """Returns the timestamp of the last cache update."""
        return self._last_cache_update
    
    @property
    def cached_temperatures(self) -> list[float]:
        """Returns the cached temperatures."""
        return self._cached_temperatures
    
    @cached_temperatures.setter
    def cached_temperatures(self, temperatures: list[float]) -> None:
        """Sets the cached temperatures and updates the last cache update timestamp."""
        self._cached_temperatures = temperatures
        self._last_cache_update = datetime.now()
        self.logger.debug(f"Cached temperatures updated.")

    def data_expired(self) -> bool:
        """Checks if the cached data has expired based on the MAX_DATA_AGE."""
        if self.last_cache_update is None:
            return True
        return self.last_cache_update + timedelta(seconds=MAX_DATA_AGE) < datetime.now()
    
    def get_current_conditions(self) -> GlobalConditions:
        """Returns the current weather conditions, updating them if necessary."""
        current_conditions = self.current_conditions
        if self.current_conditions is None or self.data_expired():
            current_conditions = self.update_current_conditions() # in case the api call fails, the standard conditions will be used - we dont want to update the self.current_conditions
        return current_conditions

    def update_current_conditions(self) -> GlobalConditions:
        """Updates the current weather conditions by fetching data from the API."""
        # For now, we will fetch the average temperature for the last 24 hours
        if self.data_expired() or not self.cached_temperatures:
            try:
                self.cache_temperatures()
            except Exception as e:
                self.logger.error(f"Error fetching temperatures: {e}")
                self.logger.warning("Using standard conditions as fallback.")
                standard_conditions_fallback = GlobalConditions(
                    temperature=self.global_config.standard_conditions.temperature_celsius,
                    rain_mm=self.global_config.standard_conditions.rain_mm,
                    sunlight_hours=self.global_config.standard_conditions.sunlight_hours,
                    timestamp=datetime.now()
                )
                return standard_conditions_fallback
        
        avg_temperature = self.get_avg_temperature(interval_days=1)
        total_rainfall = self.get_total_rainfall(interval_days=1)
        avg_sunlight_hours = self.get_avg_daily_sunlight_hours(interval_days=1)
        timestamp_retrieved = self.last_cache_update
        self.current_conditions = GlobalConditions(
            temperature=avg_temperature,
            rain_mm=total_rainfall,
            sunlight_hours=avg_sunlight_hours,
            timestamp=timestamp_retrieved
        )
        return self.current_conditions


    def get_conditions_str(self) -> str:
        """Returns a string representation of the current weather conditions."""
        if self.current_conditions is None:
            return "No current weather conditions available."
        return (f"Temperature: {self.current_conditions.temperature:.2f} °C, "
                f"Rain: {self.current_conditions.rain_mm:.2f} mm, "
                f"Sunlight: {self.current_conditions.sunlight_hours:.2f} hours, "
                f"Timestamp: {self.current_conditions.timestamp.isoformat()}")
    
    def get_avg_temperature(self, interval_days: int) -> float:
        """Fetches the average temperature over the specified interval."""
        if self.data_expired() or not self.cached_temperatures:
            try:
                self.cache_temperatures()
            except Exception as e:
                self.logger.error("Error fetching temperatures, temperature won't be used in calculations.")
                return self.global_config.standard_conditions.temperature_celsius
        
        if not self.cached_temperatures:
            self.logger.error("No temperatures available in cache, using standard conditions.")
            return self.global_config.standard_conditions.temperature_celsius
        
        relevant_temperatures = self.cached_temperatures[-(interval_days * 24 * 60 // TEMPERATURE_TIME_RESOLUTION):]    
        if not relevant_temperatures:
            self.logger.error("No relevant temperatures available for the specified interval, using standard conditions.")
            return self.global_config.standard_conditions.temperature_celsius
        avg_temperature = sum(relevant_temperatures) / len(relevant_temperatures)
        return avg_temperature
    
    def get_total_rainfall(self, interval_days: int) -> float:
        """Fetches the total rainfall over the specified interval."""
        # Placeholder for actual implementation
        return 5.0
    
    def get_avg_daily_sunlight_hours(self, interval_days: int) -> float:
        """Fetches the average daily sunlight hours over the specified interval."""
        # Placeholder for actual implementation
        return 10.0

    def cache_temperatures(self) -> None:
        """Fetches the temperatures for the last <max_interval_days> days and caches them."""
        temperatures = self.temperature_api_call(
            start_date=datetime.now() - timedelta(days=self.max_interval_days),
            end_date=datetime.now()
        )
        temperatures_list = list(temperatures.values())
        self.logger.debug(f"Fetched list: {temperatures_list}")
        # convert values to float and filter out invalid entries (e.g., '-', or empty strings)
        self.cached_temperatures = [
            float(temp) for temp in temperatures_list if temp.replace('.', '', 1).replace('-', '', 1).isdigit()
        ]
        # log the difference in the number of temperatures fetched
        self.logger.debug(f"Cached {len(self.cached_temperatures)} from {len(temperatures)} temperatures fetched from API.")


    
    def temperature_api_call(self, start_date: datetime, end_date: datetime) -> dict[str, str]:
        """Performs an API call to fetch temperature data."""
        params = {
            "application_key": self.global_config.weather_api.application_key,
            "api_key": self.global_config.weather_api.api_key,
            "mac": self.global_config.weather_api.device_mac,
            "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "cycle_type": self.get_cycle_type(),
            "call_back": "outdoor.temperature",
            "temp_unitid": CELSIUS,
        }

        safe_params = self.hide_confidential_params(params, ["api_key", "application_key", "mac"])

        url = self.global_config.weather_api.history_url
        self.logger.debug(f"Performing API call to {url} with params: {safe_params}")
        response = requests.get(url, params=params)

        # Status code -1 indicates too frequent API calls in a short time - wait and retry

        if response.status_code != 200:
            self.logger.error(f"Failed to fetch temperature data: {response.status_code} - {response.text}")
            raise Exception("Failed to fetch temperature data from API.")
        data = response.json()
        self.save_json(data)  # Save the raw data for debugging purposes
        try:
            temperatures_dict = data.get("data").get("outdoor").get("temperature").get("list", [])
        except KeyError as e:
            self.logger.error(f"Unexpected response format: {data}")
            raise ValueError("Unexpected response format from temperature API.")

        self.logger.debug(f"Successfully fetched temperature data.")
        return temperatures_dict
        

    
    def get_cycle_type(self) -> str:
        """Returns the data resolution in string format (e.g., '30min')."""
        if TEMPERATURE_TIME_RESOLUTION == 5:
            return "5min"
        elif TEMPERATURE_TIME_RESOLUTION == 30:
            return "30min"
        elif TEMPERATURE_TIME_RESOLUTION == 240:
            return "4hour"
        elif TEMPERATURE_TIME_RESOLUTION == 1440:
            return "1day"
        else:
            raise ValueError("Unsupported TEMPERATURE_TIME_RESOLUTION value.")
        
    
    def hide_confidential_params(self, params: dict, keys_to_hide: list[str]) -> dict:
        """Returns a copy of the params dictionary with specified keys hidden."""
        safe_params = params.copy()
        for key in keys_to_hide:
            if key in safe_params:
                safe_params[key] = "***"
        return safe_params
    

    def save_json(self, data):
        filename = f"recent_weather_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        self.logger.debug(f"Saved JSON data to {filename}")