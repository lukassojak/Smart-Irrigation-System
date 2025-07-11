import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import json

from smart_irrigation_system.enums import IrrigationState
from smart_irrigation_system.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.circuit_state_manager import CircuitStateManager

@pytest.fixture
def mock_drippers():
    mock = Mock()
    mock.get_consumption.return_value = 60.0  # liters per hour
    mock.get_minimum_dripper_flow.return_value = 2.0  # l/h
    return mock

@pytest.fixture
def mock_valve(monkeypatch):
    mock = Mock()
    monkeypatch.setattr("smart_irrigation_system.relay_valve.RelayValve", lambda pin: mock)
    return mock

@pytest.fixture
def mock_correction_factors():
    mock = Mock()
    mock.factors = {'sunlight': 1.0, 'rain': 1.0, 'temperature': 1.0}
    return mock

@pytest.fixture
def irrigation_circuit(mock_drippers, mock_correction_factors, mock_valve):
    return IrrigationCircuit(
        name="Test Circuit",
        circuit_id=1,
        relay_pin=5,
        enabled=True,
        even_area_mode=True,
        target_mm=10,
        zone_area_m2=5,
        liters_per_minimum_dripper=1.0,
        interval_days=3,
        drippers=mock_drippers,
        correction_factors=mock_correction_factors,
        sensor_pins=[]
    )

# Fixture for a sample state file
@pytest.fixture
def sample_state_file(tmp_path):
    sample_state = {
        "last_updated": "2025-06-22T14:00:00",
        "circuits": [
            {
                "id": "1",
                "last_irrigation": "2025-06-21T20:00:00",
                "last_result": "success",
                "last_duration": 180
            },
            {
                "id": "2",
                "last_irrigation": None,
                "last_result": None,
                "last_duration": None
            }
        ]
    }
    path = tmp_path / "state.json"
    with open(path, "w") as f:
        json.dump(sample_state, f, indent=4)
    return path

# Fixture for CircuitStateManager
@pytest.fixture
def manager(sample_state_file):
    m = CircuitStateManager(str(sample_state_file))
    m._rebuild_circuit_index()
    return m


def test_get_base_target_water_amount_even_mode(irrigation_circuit):
    result = irrigation_circuit.get_base_target_water_amount()
    assert result == 50.0  # 10 mm * 5 m² = 50 l


def test_get_base_target_water_amount_non_even_mode(irrigation_circuit, mock_drippers):
    irrigation_circuit.even_area_mode = False
    irrigation_circuit.liters_per_minimum_dripper = 1.0
    mock_drippers.get_minimum_dripper_flow.return_value = 2.0  # 1 l / 2 lph = 0.5 h
    mock_drippers.get_consumption.return_value = 60.0  # 60 l/h

    result = irrigation_circuit.get_base_target_water_amount()
    assert result == 30.0  # 60 * 0.5 h


def test_get_target_duration_seconds_even_mode(irrigation_circuit, mock_drippers):
    mock_drippers.get_consumption.return_value = 60.0
    duration = irrigation_circuit.get_target_duration_seconds(60.0)
    assert pytest.approx(duration) == 3600.0  # 1 hour = 3600 s


def test_get_target_duration_seconds_non_even_mode(irrigation_circuit, mock_drippers):
    irrigation_circuit.even_area_mode = False
    irrigation_circuit.liters_per_minimum_dripper = 2.0
    mock_drippers.get_minimum_dripper_flow.return_value = 2.0  # 1 hour
    duration = irrigation_circuit.get_target_duration_seconds(0)  # Argument ignored in non-even mode
    assert pytest.approx(duration) == 3600.0


def test_interval_days_passed_when_none(irrigation_circuit):
    assert irrigation_circuit.interval_days_passed(None) is True


def test_interval_days_passed_true(irrigation_circuit):
    last_irrigation = datetime.now() - timedelta(days=4)
    assert irrigation_circuit.interval_days_passed(last_irrigation) is True


def test_interval_days_passed_false(irrigation_circuit):
    last_irrigation = datetime.now() - timedelta(days=2)
    assert irrigation_circuit.interval_days_passed(last_irrigation) is False


def test_interval_days_passed_today(irrigation_circuit):
    last_irrigation = datetime.now() - timedelta(days=3)
    assert irrigation_circuit.interval_days_passed(last_irrigation) is True  


def test_is_currently_irrigating(irrigation_circuit):
    for state in IrrigationState:
        irrigation_circuit.state = state
        if state != IrrigationState.IRRIGATING:
            assert irrigation_circuit.is_currently_irrigating is False
        else:
            assert irrigation_circuit.is_currently_irrigating is True


def test_is_irrigation_allowed_all_pass(manager, irrigation_circuit):
    irrigation_circuit.state = IrrigationState.IDLE
    irrigation_circuit.enabled = True
    assert irrigation_circuit.is_irrigation_allowed(manager) is True


def test_is_irrigation_allowed_disabled(manager, irrigation_circuit):
    irrigation_circuit.state = IrrigationState.IDLE
    irrigation_circuit.enabled = False

    assert irrigation_circuit.is_irrigation_allowed(manager) is False


def test_is_irrigation_allowed_not_idle(manager, irrigation_circuit):
    irrigation_circuit.state = IrrigationState.IRRIGATING

    assert irrigation_circuit.is_irrigation_allowed(manager) is False


def test_is_irrigation_allowed_interval_not_passed(manager, irrigation_circuit):
    irrigation_circuit.state = IrrigationState.IDLE
    irrigation_circuit.enabled = True
    # Simulate last irrigation happened now
    manager.update_irrigation_result(irrigation_circuit, "success", 0)

    assert irrigation_circuit.is_irrigation_allowed(manager) is False   # Interval not passed


# --- Tests for state getters and setters ---

@pytest.fixture
def basic_irrigation_circuit():
    return IrrigationCircuit(
        name="Test Circuit",
        circuit_id=1,
        relay_pin=17,
        enabled=True,
        even_area_mode=True,
        target_mm=10.0,
        zone_area_m2=5.0,
        liters_per_minimum_dripper=2.0,
        interval_days=2,
        drippers=mock_drippers(),
        correction_factors=mock_correction_factors(),
        sensor_pins=None
    )

