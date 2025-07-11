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
from smart_irrigation_system.drippers import Drippers
from smart_irrigation_system.correction_factors import CorrectionFactors


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
        "interval_days": 3,
        "drippers_summary": {
            "2": 4,
            "4": 2
        },
        "local_correction_factors": {
            "sunlight": 0.8,
            "rain": 1.2,
            "temperature": 1.0
        }
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
        "interval_days": 2,
        "drippers_summary": {
            "2": 3,
            "4": 1
        },
        "local_correction_factors": {
            "sunlight": 1.0,
            "rain": 0.9,
            "temperature": 1.1
        }
    }


def test_load_global_config_valid(tmp_path, valid_global_config_dict):
    file_path = tmp_path / "global_config.json"
    with open(file_path, "w") as f:
        json.dump(valid_global_config_dict, f)

    config = load_global_config(str(file_path))
    assert isinstance(config, GlobalConfig)
    assert config.standard_conditions.sunlight_hours == 5.0
    assert config.irrigation_limits.min_percent == 50
    assert config.automation.enabled is True
    assert config.logging.log_level == "INFO"
    assert config.correction_factors.sunlight == 1.0


def test_load_zones_config_valid_even_mode(tmp_path, valid_zone_dict_even_mode):
    file_path = tmp_path / "zones.json"
    with open(file_path, "w") as f:
        json.dump({"zones": [valid_zone_dict_even_mode]}, f)

    circuits = load_zones_config(str(file_path))
    assert isinstance(circuits, list)
    assert isinstance(circuits[0], IrrigationCircuit)
    assert circuits[0].name == "Zone 1"
    assert circuits[0].even_area_mode is True
    assert circuits[0].target_mm == 10.0
    assert circuits[0].zone_area_m2 == 25.0
    assert circuits[0].liters_per_minimum_dripper is None
    assert circuits[0].local_correction_factors.factors == {
        "sunlight": 0.8,
        "rain": 1.2,
        "temperature": 1.0
    }

def test_load_zones_config_valid_dripper_mode(tmp_path, valid_zone_dict_dripper_mode):
    file_path = tmp_path / "zones.json"
    with open(file_path, "w") as f:
        json.dump({"zones": [valid_zone_dict_dripper_mode]}, f)

    circuits = load_zones_config(str(file_path))
    assert len(circuits) == 1
    assert circuits[0].even_area_mode is False
    assert circuits[0].liters_per_minimum_dripper == 2.0
    assert circuits[0].target_mm is None
    assert circuits[0].zone_area_m2 is None
    assert circuits[0].drippers.get_consumption() == 10.0  # 2 drippers of 2 L/h and 1 dripper of 4 L/h


def test_is_valid_zone_even_mode(valid_zone_dict_even_mode):
    valid, errors = _is_valid_zone(valid_zone_dict_even_mode)
    assert valid is True
    assert errors == []


def test_is_valid_zone_dripper_mode(valid_zone_dict_dripper_mode):
    valid, errors = _is_valid_zone(valid_zone_dict_dripper_mode)
    assert valid is True
    assert errors == []


def test_invalid_zone_missing_keys(valid_zone_dict_even_mode):
    no_relay_pin = valid_zone_dict_even_mode.copy()
    del no_relay_pin["relay_pin"]
    valid, errors = _is_valid_zone(no_relay_pin)
    assert valid is False

    no_enabled = valid_zone_dict_even_mode.copy()
    del no_enabled["enabled"]
    valid, errors = _is_valid_zone(no_enabled)
    assert valid is False

    no_even_area_mode = valid_zone_dict_even_mode.copy()
    del no_even_area_mode["even_area_mode"]
    valid, errors = _is_valid_zone(no_even_area_mode)
    assert valid is False


def test_invalid_even_mode_logic(valid_zone_dict_even_mode):
    zone_area_m2_none = valid_zone_dict_even_mode.copy()
    zone_area_m2_none["zone_area_m2"] = None  # invalid with even_area_mode=True
    valid, errors = _is_valid_zone(zone_area_m2_none)
    assert valid is False

    liters_per_minimum_dripper_not_none = valid_zone_dict_even_mode.copy()
    liters_per_minimum_dripper_not_none["liters_per_minimum_dripper"] = 2.0  # invalid with even_area_mode=True
    valid, errors = _is_valid_zone(liters_per_minimum_dripper_not_none)
    assert valid is False


def test_invalid_dripper_mode_logic(valid_zone_dict_dripper_mode):
    target_mm_not_none = valid_zone_dict_dripper_mode.copy()
    target_mm_not_none["target_mm"] = 10.0  # invalid with even_area_mode=False
    valid, errors = _is_valid_zone(target_mm_not_none)
    assert valid is False

    zone_area_m2_not_none = valid_zone_dict_dripper_mode.copy()
    zone_area_m2_not_none["zone_area_m2"] = 25.0  # invalid with even_area_mode=False
    valid, errors = _is_valid_zone(zone_area_m2_not_none)
    assert valid is False

    liters_per_minimum_dripper_none = valid_zone_dict_dripper_mode.copy()
    liters_per_minimum_dripper_none["liters_per_minimum_dripper"] = None  # invalid with even_area_mode=False
    valid, errors = _is_valid_zone(liters_per_minimum_dripper_none)
    assert valid is False


def test_circuit_from_config_creates_object(valid_zone_dict_even_mode):
    circuit = circuit_from_config(valid_zone_dict_even_mode)
    assert isinstance(circuit, IrrigationCircuit)
    assert circuit.name == "Zone 1"
    assert circuit.even_area_mode is True
    assert circuit.target_mm == 10.0
    assert circuit.drippers.get_consumption() == 16.0  # 4 drippers of 2 L/h and 2 drippers of 4 L/h
