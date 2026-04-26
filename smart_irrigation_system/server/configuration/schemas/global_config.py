from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StandardConditions(BaseModel):
    solar_total: float
    rain_mm: float
    temperature_celsius: float


class CorrectionFactors(BaseModel):
    solar: float
    rain: float
    temperature: float


class WeatherApiConfiguration(BaseModel):
    api_enabled: bool
    realtime_url: str
    history_url: str
    api_key: str | None = None
    application_key: str | None = None
    device_mac: str | None = None


class GlobalConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    standard_conditions: StandardConditions
    correction_factors: CorrectionFactors
    weather_api: WeatherApiConfiguration
    last_updated: datetime


class GlobalConfigUpdate(BaseModel):
    standard_conditions: StandardConditions | None = None
    correction_factors: CorrectionFactors | None = None
    weather_api: WeatherApiConfiguration | None = None
