import pytest
from unittest.mock import patch
from smart_irrigation_system.node.config.global_config import (
    GlobalConfig,
    StandardConditions,
    CorrectionFactors,
    IrrigationLimits,
    AutomationSettings,
    LoggingSettings,
    LogLevel
)


@pytest.fixture
def sample_config_dict():
    return {
        "standard_conditions": {
            "sunlight_hours": 10.5,
            "rain_mm": 5.2,
            "temperature_celsius": 22.3
        },
        "correction_factors": {
            "sunlight": 1.2,
            "rain": 0.8,
            "temperature": 1.0
        },
        "irrigation_limits": {
            "min_percent": 30,
            "max_percent": 90,
            "main_valve_max_flow": 12.5
        },
        "automation": {
            "enabled": True,
            "sequential": False,
            "scheduled_hour": 6,
            "scheduled_minute": 30,
            "max_flow_monitoring": True
        },
        "logging": {
            "enabled": True,
            "log_level": "DEBUG"
        }
    }

def test_global_config_from_dict(sample_config_dict):
    config = GlobalConfig.from_dict(sample_config_dict)

    assert isinstance(config, GlobalConfig)
    assert config.standard_conditions.sunlight_hours == 10.5
    assert config.standard_conditions.rain_mm == 5.2
    assert config.standard_conditions.temperature_celsius == 22.3

    assert config.correction_factors.sunlight == 1.2
    assert config.correction_factors.rain == 0.8
    assert config.correction_factors.temperature == 1.0

    assert config.irrigation_limits.min_percent == 30
    assert config.irrigation_limits.max_percent == 90
    assert config.irrigation_limits.main_valve_max_flow == 12.5

    assert config.automation.enabled is True
    assert config.automation.sequential is False
    assert config.automation.scheduled_hour == 6
    assert config.automation.scheduled_minute == 30
    assert config.automation.max_flow_monitoring is True

    assert config.logging.enabled is True
    assert config.logging.log_level == LogLevel.DEBUG

def test_log_level_enum():
    assert LogLevel.DEBUG.value == "DEBUG"
    assert LogLevel["INFO"] == LogLevel.INFO

def test_invalid_log_level_raises(sample_config_dict):
    sample_config_dict["logging"]["log_level"] = "INVALID"
    with pytest.raises(ValueError):
        GlobalConfig.from_dict(sample_config_dict)