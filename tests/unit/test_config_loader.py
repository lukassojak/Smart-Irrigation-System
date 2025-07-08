import pytest
import json
from smart_irrigation_system.config_loader import (
    load_global_config,
    load_zones_config,
    _is_valid_zone,
    circuit_from_config
)
from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.irrigation_circuit import IrrigationCircuit


@pytest.fixture
def valid_global_config_dict():
    return {
        "standard_conditions": {
            "sunlight_hours": 5.0,
            "rain_mm": 10.0,
            "temperature_celsius": 22.0
        },
        "correction_factors": {
            "sunlight": 1.0,
            "rain": 0.5,
            "temperature": 1.2
        },
        "irrigation_limits": {
            "min_percent": 50,
            "max_percent": 150,
            "main_valve_max_flow": 20.0
        },
        "automation": {
            "enabled": True,
            "sequential": True,
            "scheduled_hour": 6,
            "scheduled_minute": 30,
            "max_flow_monitoring": False
        },
        "logging": {
            "enabled": True,
            "log_level": "INFO"
        }
    }


@pytest.fixture
def valid_zone_dict_even_mode():
    return {
        "name": "Zone 1",
        "id": 1,
        "relay_pin": 17,
        "enabled": True,
        "even_area_mode": True,
        "target_mm": 10.0,
        "zone_area_m2": 25.0,
        "liters_per_minimum_dripper": None,
        "standard_flow_seconds": 120,
        "interval_days": 3,
        "drippers_summary": {
            "2": 4,
            "4": 2
        },
        "sunlight": 0.8,
        "rain": 1.2,
        "temperature": 1.0
    }


@pytest.fixture
def valid_zone_dict_dripper_mode():
    return {
        "name": "Zone 2",
        "id": 2,
        "relay_pin": 18,
        "enabled": True,
        "even_area_mode": False,
        "target_mm": None,
        "zone_area_m2": None,
        "liters_per_minimum_dripper": 2.0,
        "standard_flow_seconds": 90,
        "interval_days": 2,
        "drippers_summary": {
            "2": 3,
            "4": 1
        },
        "sunlight": 1.0,
        "rain": 0.9,
        "temperature": 1.1
    }


def test_load_global_config_valid(tmp_path, valid_global_config_dict):
    file_path = tmp_path / "global_config.json"
    with open(file_path, "w") as f:
        json.dump(valid_global_config_dict, f)

    config = load_global_config(str(file_path))
    assert isinstance(config, GlobalConfig)
    assert config.standard_conditions.sunlight_hours == 5.0
    assert config.irrigation_limits.min_percent == 50


def test_load_zones_config_valid_even_mode(tmp_path, valid_zone_dict_even_mode):
    file_path = tmp_path / "zones.json"
    with open(file_path, "w") as f:
        json.dump({"zones": [valid_zone_dict_even_mode]}, f)

    circuits = load_zones_config(str(file_path))
    assert isinstance(circuits, list)
    assert isinstance(circuits[0], IrrigationCircuit)
    assert circuits[0].name == "Zone 1"
    assert circuits[0].even_area_mode is True


def test_load_zones_config_valid_dripper_mode(tmp_path, valid_zone_dict_dripper_mode):
    file_path = tmp_path / "zones.json"
    with open(file_path, "w") as f:
        json.dump({"zones": [valid_zone_dict_dripper_mode]}, f)

    circuits = load_zones_config(str(file_path))
    assert len(circuits) == 1
    assert circuits[0].even_area_mode is False
    assert circuits[0].liters_per_minimum_dripper == 2.0


def test_is_valid_zone_even_mode(valid_zone_dict_even_mode):
    assert _is_valid_zone(valid_zone_dict_even_mode) is True


def test_is_valid_zone_dripper_mode(valid_zone_dict_dripper_mode):
    assert _is_valid_zone(valid_zone_dict_dripper_mode) is True


def test_invalid_zone_missing_keys(valid_zone_dict_even_mode):
    del valid_zone_dict_even_mode["relay_pin"]
    assert _is_valid_zone(valid_zone_dict_even_mode) is False


def test_invalid_even_mode_logic(valid_zone_dict_even_mode):
    valid_zone_dict_even_mode["liters_per_minimum_dripper"] = 2.0  # invalid with even_area_mode=True
    assert _is_valid_zone(valid_zone_dict_even_mode) is False


def test_invalid_dripper_mode_logic(valid_zone_dict_dripper_mode):
    valid_zone_dict_dripper_mode["target_mm"] = 5.0  # invalid with even_area_mode=False
    assert _is_valid_zone(valid_zone_dict_dripper_mode) is False


def test_circuit_from_config_creates_object(valid_zone_dict_even_mode):
    circuit = circuit_from_config(valid_zone_dict_even_mode)
    assert isinstance(circuit, IrrigationCircuit)
    assert circuit.name == "Zone 1"
    assert circuit.even_area_mode is True
    assert circuit.target_mm == 10.0
    assert circuit.drippers.total_drippers() == 6
