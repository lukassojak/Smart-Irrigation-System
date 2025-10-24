import pytest
import json
from datetime import datetime
from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from types import SimpleNamespace


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


# Fixture for IrrigationCircuit – using SimpleNamespace to mock the circuit
@pytest.fixture
def dummy_circuit():
    drippers = SimpleNamespace()
    correction = SimpleNamespace()
    return IrrigationCircuit(
        name="Test",
        circuit_id=1,
        relay_pin=1,
        enabled=True,
        even_area_mode=True,
        target_mm=10.0,
        zone_area_m2=5.0,
        liters_per_minimum_dripper=None,
        interval_days=3,
        drippers=drippers,
        correction_factors=correction
    )


def test_loads_valid_state(manager):
    assert "circuits" in manager.state
    assert len(manager.state["circuits"]) == 2


def test_get_last_irrigation_time(manager, dummy_circuit):
    last_irrigation = manager.get_last_irrigation_time(dummy_circuit)
    assert isinstance(last_irrigation, datetime)
    assert last_irrigation.isoformat() == "2025-06-21T20:00:00"


def test_update_irrigation_result_success(manager, dummy_circuit):
    manager.update_irrigation_result(dummy_circuit, "success", 200)

    circuit = manager.state["circuits"][manager.circuit_index[dummy_circuit.id]]
    assert circuit["last_result"] == "success"
    assert circuit["last_duration"] == 200
    assert "last_irrigation" in circuit

    # Check if the file was updated
    with open(manager.state_file) as f:
        data = json.load(f)
    updated = next(c for c in data["circuits"] if c["id"] == "1")
    assert updated["last_result"] == "success"
    assert updated["last_duration"] == 200


def test_update_irrigation_result_skipped(manager, dummy_circuit):
    previous_irrigation = manager.state["circuits"][manager.circuit_index[dummy_circuit.id]]["last_irrigation"]
    manager.update_irrigation_result(dummy_circuit, "skipped", 0)

    circuit = manager.state["circuits"][manager.circuit_index[dummy_circuit.id]]
    assert circuit["last_result"] == "skipped"
    assert circuit["last_irrigation"] == previous_irrigation  # Should not change
    assert circuit["last_duration"] == 180  # Should not change either


def test_update_irrigation_result_invalid(manager, dummy_circuit):
    manager.update_irrigation_result(dummy_circuit, "invalid_result", 123)

    circuit = manager.state["circuits"][manager.circuit_index[dummy_circuit.id]]
    # last_result should not change to an invalid value
    assert circuit["last_result"] == "success"
    assert circuit["last_duration"] == 180


def test_get_last_irrigation_time_invalid_id(manager):
    invalid_circuit = SimpleNamespace(id=999)
    assert manager.get_last_irrigation_time(invalid_circuit) is None


# --- More tests below ---

# Missing key "circuits"
def test_missing_circuits_key(tmp_path):
    bad_state = {
        "last_updated": "2025-06-22T14:00:00"
        # "circuits" key is missing here
    }
    path = tmp_path / "bad.json"
    with open(path, "w") as f:
        json.dump(bad_state, f)

    manager = CircuitStateManager(str(path))
    assert manager.state["circuits"] == []
    assert isinstance(manager.state["last_updated"], str)

# Invalid datetime format for "last_updated"
def test_invalid_datetime_format(tmp_path):
    state = {
        "last_updated": "2025-06-22T14:00:00",
        "circuits": [
            {
                "id": "1",
                "last_irrigation": "not-a-valid-datetime",
                "last_result": "success",
                "last_duration": 120
            }
        ]
    }
    path = tmp_path / "invalid_date.json"
    with open(path, "w") as f:
        json.dump(state, f)

    manager = CircuitStateManager(str(path))
    circuit = SimpleNamespace(id=1)
    assert manager.get_last_irrigation_time(circuit) is None  # Should return None due to invalid date

# Test saving state after updating irrigation result
def test_saving_state(manager, dummy_circuit, sample_state_file):
    manager.update_irrigation_result(dummy_circuit, "success", 250)
    manager.save_state()

    with open(sample_state_file) as f:
        data = json.load(f)

    updated = next(c for c in data["circuits"] if c["id"] == "1")
    assert updated["last_result"] == "success"
    assert updated["last_duration"] == 250
    assert "last_irrigation" in updated

# Empty JSON file
def test_empty_json_file(tmp_path):
    path = tmp_path / "empty.json"
    with open(path, "w") as f:
        f.write("{}")

    manager = CircuitStateManager(str(path))
    assert isinstance(manager.state, dict)
    assert "circuits" in manager.state
    assert manager.state["circuits"] == []

# Test updating another circuit
def test_update_other_circuit(manager):
    dummy_other = SimpleNamespace(id=2)
    manager.update_irrigation_result(dummy_other, "success", 111)

    circuit = next(c for c in manager.state["circuits"] if c["id"] == "2")
    assert circuit["last_result"] == "success"
    assert circuit["last_duration"] == 111