import pytest
from unittest.mock import MagicMock, patch
from smart_irrigation_system.node.weather.weather_simulator import WeatherSimulator
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions
from datetime import datetime


def test_weather_simulator_ranges():
    from node.weather.weather_simulator import WeatherSimulator
    sim = WeatherSimulator()
    for _ in range(100):
        conditions = sim.get_current_conditions()
        assert 10 <= conditions.temperature <= 40, "Temperature out of range"
        assert 0 <= conditions.rain_mm <= 30, "Rainfall out of range"
        assert 0 <= conditions.sunlight_hours <= 16, "Sunlight hours out of range"


def test_weather_simulator_determinism():
    for seed in range(100):
        sim1 = WeatherSimulator(seed=seed)
        sim2 = WeatherSimulator(seed=seed)

        conditions1 = sim1.get_current_conditions()
        conditions2 = sim2.get_current_conditions()

        assert conditions1.temperature == conditions2.temperature
        assert conditions1.rain_mm == conditions2.rain_mm
        assert conditions1.sunlight_hours == conditions2.sunlight_hours
        delta = abs((conditions1.timestamp - conditions2.timestamp).total_seconds())
        assert delta < 1, "Timestamps differ more than 1 second"


def test_weather_simulator_output_structure():

    sim = WeatherSimulator()
    conditions = sim.get_current_conditions()

    assert isinstance(conditions, GlobalConditions)
    assert isinstance(conditions.temperature, float)
    assert isinstance(conditions.rain_mm, float)
    assert isinstance(conditions.sunlight_hours, float)
    assert isinstance(conditions.timestamp, datetime)


def test_weather_simulator_timestamp_recent():
    sim = WeatherSimulator()
    conditions = sim.get_current_conditions()

    now = datetime.now()
    delta = abs((now - conditions.timestamp).total_seconds())

    assert delta < 2  # Maximum 2 seconds difference allowed for timestamp retrieval