import pytest
from unittest.mock import MagicMock
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions


def test_global_conditions_initialization():
    """Test the initialization of GlobalConditions with valid data."""
    conditions = GlobalConditions(
        temperature=25.0,
        rain_mm=5.0,
        sunlight_hours=8.0,
        timestamp="2023-10-01T12:00:00"
    )
    
    assert conditions.temperature == 25.0
    assert conditions.rain_mm == 5.0
    assert conditions.sunlight_hours == 8.0
    assert conditions.timestamp == "2023-10-01T12:00:00"