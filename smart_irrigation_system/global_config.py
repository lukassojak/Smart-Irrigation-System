from dataclasses import dataclass
from enum import Enum



class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class StandardConditions:
    sunlight_hours: float
    rain_mm: float
    temperature_celsius: float

@dataclass
class CorrectionFactors:
    sunlight: float
    rain: float
    temperature: float

@dataclass
class IrrigationLimits:
    min_percent: int
    max_percent: int
    main_valve_max_flow: float

@dataclass
class AutomationSettings:
    enabled: bool
    sequential: bool
    scheduled_hour: int
    scheduled_minute: int
    max_flow_monitoring: bool
    environment: str

@dataclass
class LoggingSettings:
    enabled: bool
    log_level: LogLevel

@dataclass
class WeatherApi:
    """
    A class to hold the configuration for the weather API.
    """
    api_enabled: bool
    realtime_url: str
    history_url: str
    api_key: str
    application_key: str
    device_mac: str


@dataclass
class GlobalConfig:
    """
    A class to hold global configuration settings for the whole watering node.
    """
    standard_conditions: StandardConditions
    correction_factors: CorrectionFactors
    irrigation_limits: IrrigationLimits
    automation: AutomationSettings
    logging: LoggingSettings
    weather_api: WeatherApi

    @staticmethod
    def from_dict(data: dict) -> 'GlobalConfig':
        """
        Creates a GlobalConfig instance from a dictionary.
        """
        return GlobalConfig(
            standard_conditions=StandardConditions(
                sunlight_hours=data["standard_conditions"]["sunlight_hours"],
                rain_mm=data["standard_conditions"]["rain_mm"],
                temperature_celsius=data["standard_conditions"]["temperature_celsius"]
            ),
            correction_factors=CorrectionFactors(
                sunlight=data["correction_factors"]["sunlight"],
                rain=data["correction_factors"]["rain"],
                temperature=data["correction_factors"]["temperature"]
            ),
            irrigation_limits=IrrigationLimits(
                min_percent=data["irrigation_limits"]["min_percent"],
                max_percent=data["irrigation_limits"]["max_percent"],
                main_valve_max_flow=data["irrigation_limits"]["main_valve_max_flow"]
            ),
            automation=AutomationSettings(
                enabled=data["automation"]["enabled"],
                sequential=data["automation"]["sequential"],
                scheduled_hour=data["automation"]["scheduled_hour"],
                scheduled_minute=data["automation"]["scheduled_minute"],
                max_flow_monitoring=data["automation"]["max_flow_monitoring"],
                environment=data["automation"]["environment"]
            ),
            logging=LoggingSettings(
                enabled=data["logging"]["enabled"],
                log_level=LogLevel(data["logging"]["log_level"])
            ),
            weather_api=WeatherApi(
                api_enabled=data["weather_api"]["api_enabled"],
                realtime_url=data["weather_api"]["realtime_url"],
                history_url=data["weather_api"]["history_url"],
                api_key=data["weather_api"]["api_key"],
                application_key=data["weather_api"]["application_key"],
                device_mac=data["weather_api"]["device_mac"]
            )
        )
