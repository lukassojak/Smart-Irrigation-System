from smart_irrigation_system.node.config.global_config import GlobalConfig, StandardConditions
from smart_irrigation_system.node.config.secrets import get_secret

class WeatherConfigService:
    """
    A service that provides all the configuration data and secrets
    needed for the weather module to function. This separates the data source (local JSON/env)
    from the weather retrieval logic itself.
    """
    def __init__(self, global_config: GlobalConfig, secrets_path: str = "config/config_secrets.json"):
        self._global_config = global_config
        self._secrets_path = secrets_path
        # self._std_conditions = std_conditions
    
    def is_api_enabled(self) -> bool:
        return self._global_config.weather_api.api_enabled
    
    def get_standard_conditions(self) -> StandardConditions:
        return self._global_config.standard_conditions
    
    def get_secret_value(self, key: str) -> str:
        return get_secret(key, self._secrets_path)
    
    def get_api_urls(self) -> dict:
        return {
            "realtime_url": self._global_config.weather_api.realtime_url,
            "history_url": self._global_config.weather_api.history_url
        }
    def get_api_credentials(self) -> dict:
        return {
            "application_key": self._global_config.weather_api.application_key,
            "api_key": self._global_config.weather_api.api_key,
            "device_mac": self._global_config.weather_api.device_mac
        }