import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit, IrrigationStoppedException
from smart_irrigation_system.node.exceptions import RelayValveError
from smart_irrigation_system.node.core.enums import IrrigationState
from smart_irrigation_system.node.core.status_models import CircuitSnapshot


# ---------------------- Fakes ----------------------

class FakeCorrectionFactors:
    def __init__(self, solar=0.0, rain=0.0, temperature=0.0):
        self.factors = {
            "solar": solar,
            "rain": rain,
            "temperature": temperature,
        }
    
    def set_factor(self, parameter, value):
        if parameter in self.factors:
            self.factors[parameter] = value
        else:
            raise ValueError(f"Unknown parameter: {parameter}")
        
    def get_factor(self, parameter):
        return self.factors.get(parameter)


# ---------------------- Helpers ----------------------

def _make_circuit(
    *,
    enabled: bool = True,
    even_area_mode: bool = True,
    base_volume_liters: float = 200.0,
    base_flow_lph: float = 10.0,
    interval_days: int = 2,
    circuit_id: int = 1,
    frequency_settings: dict | None = None,
) -> IrrigationCircuit:
    """Helper to create IrrigationCircuit with Phase 1 API."""
    with patch("smart_irrigation_system.node.core.irrigation_circuit.RelayValve"):
        circuit = IrrigationCircuit(
            name="TestCircuit",
            circuit_id=circuit_id,
            relay_pin=1,
            enabled=enabled,
            even_area_mode=even_area_mode,
            base_volume_liters=base_volume_liters,
            base_flow_lph=base_flow_lph,
            interval_days=interval_days,
            correction_factors=FakeCorrectionFactors(),
            frequency_settings=frequency_settings,
        )
    return circuit


# ---------------------- Tests ----------------------

@pytest.mark.parametrize(
        ("enabled", "expected_state"),
        [
            (True, IrrigationState.IDLE),
            (False, IrrigationState.DISABLED)
        ]
)
def test_initial_state_and_fault_flags(enabled, expected_state):
    # Arrange & Act
    circuit = _make_circuit(enabled=enabled)

    # Assert
    assert circuit.state == expected_state
    assert circuit.has_fault == False
    assert circuit.last_fault_reason == None

@pytest.mark.parametrize(
        ("base_volume_liters", "expected_result_volume"),
        [
            (50, 50),           # base_volume_liters=50 -> 50 liters
            (200, 200),         # base_volume_liters=200 -> 200 liters
            (111.6, 111.6),     # base_volume_liters=111.6 -> 111.6 liters
        ]
)
def test_base_target_volume_returns_configured_base_volume(base_volume_liters, expected_result_volume):
    # Arrange & Act
    circuit = _make_circuit(base_volume_liters=base_volume_liters)

    # Assert
    assert circuit.base_target_volume == pytest.approx(expected_result_volume)
    

@pytest.mark.parametrize(
        ("has_fault", "circuit_state", "expected_result"),
        [
            (False, IrrigationState.IDLE, True),
            (False, IrrigationState.WAITING, False),
            (False, IrrigationState.IRRIGATING, False),
            (False, IrrigationState.DISABLED, False),
            (True, IrrigationState.IDLE, False),
            (True, IrrigationState.WAITING, False),
            (True, IrrigationState.IRRIGATING, False),
            (True, IrrigationState.DISABLED, False)
        ]
)
def test_is_safe_to_irrigate_returns_true_when_conditions_met(has_fault, circuit_state, expected_result):
    # Arrange
    circuit = _make_circuit()

    circuit.has_fault = has_fault
    circuit._state = circuit_state

    # Act
    result = circuit.is_safe_to_irrigate()

    # Assert
    assert result == expected_result


@pytest.mark.parametrize(
        ("timedelta_days", "interval_days", "expected_result"),
        [
            (3, 2, True),      # Last irrigation 3 days ago, interval 2 days -> True
            (10, 9, True),     # Last irrigation 10 days ago, interval 9 days -> True
            (10, 10, True),    # Last irrigation 10 days ago, interval 10 days -> True
            (10, 11, False),   # Last irrigation 10 days ago, interval 11 days -> False
            (1, 4, False),     # Last irrigation 1 day ago, interval 4 days -> False
            (0, 1, False),     # Last irrigation now, interval 1 day -> False
            (None, 1, True),   # No last irrigation recorded -> True
        ]
)
def test_needs_irrigation_respects_interval_and_last_irrigation(timedelta_days, interval_days, expected_result, monkeypatch):
    # Arrange
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    snapshot = CircuitSnapshot(
        id=1,
        circuit_state=IrrigationState.IDLE,
        last_decision=None,
        last_outcome=None,
        last_irrigation=base_time - timedelta(days=timedelta_days) if timedelta_days is not None else None,
        last_duration=None,
        last_volume=30.0,
        timestamp=None
    )
    mock_state_manager = MagicMock()
    mock_state_manager.get_circuit_snapshot.return_value = snapshot
    
    circuit = _make_circuit(interval_days=interval_days)
    monkeypatch.setattr(
        "smart_irrigation_system.node.core.irrigation_circuit.time_utils.now",
        lambda: base_time
    )
    # Act
    result = circuit.needs_irrigation(mock_state_manager)

    # Assert
    assert result == expected_result