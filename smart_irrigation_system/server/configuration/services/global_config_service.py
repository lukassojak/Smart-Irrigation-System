import json
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from smart_irrigation_system.server.configuration.models.global_config import GlobalConfig
from smart_irrigation_system.server.configuration.repositories.global_config_repository import GlobalConfigRepository
from smart_irrigation_system.server.configuration.schemas.global_config import GlobalConfigUpdate
from smart_irrigation_system.server.configuration.models.node import Node, CONFIG_SYNC_PENDING


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_GLOBAL_CONFIG_PATH = PROJECT_ROOT / "runtime" / "node" / "config" / "config_global.json"


def _default_global_config() -> dict:
    fallback = {
        "standard_conditions": {
            "solar_total": 5.5,
            "rain_mm": 0.0,
            "temperature_celsius": 15.0,
        },
        "correction_factors": {
            "solar": 0.0,
            "rain": 0.0,
            "temperature": 0.0,
        },
        "weather_api": {
            "api_enabled": True,
            "realtime_url": "https://api.ecowitt.net/api/v3/device/real_time",
            "history_url": "https://api.ecowitt.net/api/v3/device/history",
            "api_key": None,
            "application_key": None,
            "device_mac": None,
        },
    }

    if not DEFAULT_GLOBAL_CONFIG_PATH.exists():
        return fallback

    try:
        with DEFAULT_GLOBAL_CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return fallback

    return {
        "standard_conditions": data.get("standard_conditions", fallback["standard_conditions"]),
        "correction_factors": data.get("correction_factors", fallback["correction_factors"]),
        "weather_api": {
            "api_enabled": data.get("weather_api", {}).get("api_enabled", fallback["weather_api"]["api_enabled"]),
            "realtime_url": data.get("weather_api", {}).get("realtime_url", fallback["weather_api"]["realtime_url"]),
            "history_url": data.get("weather_api", {}).get("history_url", fallback["weather_api"]["history_url"]),
            "api_key": data.get("weather_api", {}).get("api_key"),
            "application_key": data.get("weather_api", {}).get("application_key"),
            "device_mac": data.get("weather_api", {}).get("device_mac"),
        },
    }


class GlobalConfigService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = GlobalConfigRepository(session)

    def get_or_create(self) -> GlobalConfig:
        existing = self.repo.get_singleton()
        if existing:
            return existing

        defaults = _default_global_config()
        created = GlobalConfig(
            standard_conditions=defaults["standard_conditions"],
            correction_factors=defaults["correction_factors"],
            weather_api=defaults["weather_api"],
        )
        self.repo.create(created)
        self.session.commit()
        return created

    def update(self, data: GlobalConfigUpdate) -> GlobalConfig:
        config = self.get_or_create()

        update_data = data.model_dump(exclude_unset=True)
        for field_name in ("standard_conditions", "correction_factors", "weather_api"):
            if field_name in update_data and update_data[field_name] is not None:
                setattr(config, field_name, update_data[field_name])

        config.last_updated = datetime.now(timezone.utc)
        self.repo.save(config)

        # Mark all nodes as pending config sync since exported config_global will change
        nodes = self.session.exec(select(Node)).all()
        for node in nodes:
            node.config_sync_status = CONFIG_SYNC_PENDING
            node.last_updated = datetime.now(timezone.utc)
        self.session.flush()

        self.session.commit()
        return config
