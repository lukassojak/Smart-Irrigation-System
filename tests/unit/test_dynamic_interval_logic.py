import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.enums import IrrigationOutcome, IrrigationState, SnapshotCircuitState
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.node.core.irrigation_models.weather_irrigation_model import WeatherModelResult
from smart_irrigation_system.node.core.status_models import CircuitSnapshot
from smart_irrigation_system.node.utils import result_factory


class FakeCorrectionFactors:
    def __init__(self, solar=0.0, rain=0.0, temperature=0.0):
        self.factors = {
            "solar": solar,
            "rain": rain,
            "temperature": temperature,
        }


@pytest.fixture(autouse=True)
def reset_state_manager_singleton():
    CircuitStateManager._instance = None
    yield
    CircuitStateManager._instance = None


@pytest.fixture
def base_time() -> datetime:
    return datetime(2025, 1, 10, 12, 0, 0)


def _make_circuit(
    *,
    dynamic_interval: bool = True,
    carry_over_volume: bool = True,
    threshold_percent: int = 50,
    min_interval_days: int = 1,
    max_interval_days: int = 5,
    base_volume_liters: float = 100.0,
    base_flow_lph: float = 10.0,
    interval_days: int = 3,
) -> IrrigationCircuit:
    with patch("smart_irrigation_system.node.core.irrigation_circuit.RelayValve"):
        circuit = IrrigationCircuit(
            name="TestCircuit",
            circuit_id=1,
            relay_pin=1,
            enabled=True,
            even_area_mode=True,
            base_volume_liters=base_volume_liters,
            base_flow_lph=base_flow_lph,
            interval_days=interval_days,
            correction_factors=FakeCorrectionFactors(),
            frequency_settings={
                "dynamic_interval": dynamic_interval,
                "min_interval_days": min_interval_days,
                "max_interval_days": max_interval_days,
                "carry_over_volume": carry_over_volume,
                "irrigation_volume_threshold_percent": threshold_percent,
            },
        )
    circuit.calculation_model = MagicMock()
    return circuit


def _make_state_manager(tmp_path, circuits_state: list[dict] | None = None) -> CircuitStateManager:
    state_file = tmp_path / "zones_state.json"
    log_file = tmp_path / "irrigation_log.json"
    if circuits_state is not None:
        state_file.write_text(json.dumps({"last_updated": "2025-01-10T12:00:00", "circuits": circuits_state}, indent=4))
    return CircuitStateManager(str(state_file), str(log_file))


def _snapshot(last_irrigation: datetime | None) -> CircuitSnapshot:
    return CircuitSnapshot(
        id=1,
        circuit_state=SnapshotCircuitState.IDLE,
        last_decision=None,
        last_outcome=None,
        last_irrigation=last_irrigation,
        last_duration=None,
        last_volume=None,
        timestamp=None,
    )


def _weather_result(base_volume: float, final_volume: float) -> WeatherModelResult:
    return WeatherModelResult(
        base_volume=base_volume,
        total_adjustment=0.0,
        adjusted_volume=final_volume,
        min_volume=0.0,
        max_volume=999.0,
        final_volume=final_volume,
        should_skip=False,
    )


def test_needs_irrigation_uses_min_interval_when_dynamic_interval_is_enabled(monkeypatch, base_time):
    circuit = _make_circuit(dynamic_interval=True, min_interval_days=2, max_interval_days=5)
    state_manager = MagicMock()
    state_manager.get_circuit_snapshot.return_value = _snapshot(base_time)

    monkeypatch.setattr("smart_irrigation_system.node.core.irrigation_circuit.time_utils.now", lambda *args, **kwargs: base_time)

    assert circuit.needs_irrigation(state_manager) is False


def test_dynamic_interval_skips_and_persists_carry_over_below_threshold(monkeypatch, tmp_path, base_time):
    circuit = _make_circuit(threshold_percent=50, min_interval_days=1, max_interval_days=5)
    state_manager = _make_state_manager(tmp_path)
    state_manager.get_circuit_snapshot = MagicMock(return_value=_snapshot(base_time - timedelta(days=2)))

    monkeypatch.setattr("smart_irrigation_system.node.core.irrigation_circuit.time_utils.now", lambda *args, **kwargs: base_time)
    circuit.calculation_model.compute_weather_adjusted_volume.return_value = _weather_result(base_volume=100.0, final_volume=20.0)

    should_irrigate, target_volume, reason = circuit.evaluate_dynamic_interval(
        state_manager=state_manager,
        global_config=MagicMock(),
        global_conditions=MagicMock(),
    )

    assert should_irrigate is False
    assert target_volume == pytest.approx(20.0)
    assert reason is not None
    assert state_manager.get_carry_over_volume_liters(1) == pytest.approx(20.0)


def test_dynamic_interval_accumulates_carry_over_and_clears_after_success(monkeypatch, tmp_path, base_time):
    circuit = _make_circuit(threshold_percent=50, min_interval_days=1, max_interval_days=5)
    state_manager = _make_state_manager(tmp_path)
    state_manager.get_circuit_snapshot = MagicMock(return_value=_snapshot(base_time - timedelta(days=2)))
    state_manager.set_carry_over_volume_liters(1, 20.0)

    monkeypatch.setattr("smart_irrigation_system.node.core.irrigation_circuit.time_utils.now", lambda *args, **kwargs: base_time)
    circuit.calculation_model.compute_weather_adjusted_volume.return_value = _weather_result(base_volume=100.0, final_volume=40.0)

    should_irrigate, target_volume, reason = circuit.evaluate_dynamic_interval(
        state_manager=state_manager,
        global_config=MagicMock(),
        global_conditions=MagicMock(),
    )

    assert should_irrigate is True
    assert reason is None
    assert target_volume == pytest.approx(60.0)
    assert state_manager.get_carry_over_volume_liters(1) == pytest.approx(20.0)

    success_result = result_factory.create_general(
        circuit_id=1,
        start_time=base_time,
        completed_duration=10,
        target_duration=10,
        actual_water_amount=60.0,
        target_water_amount=60.0,
        success=True,
        outcome=IrrigationOutcome.SUCCESS,
        error=None,
    )
    state_manager.irrigation_finished(1, success_result)

    assert state_manager.get_carry_over_volume_liters(1) == pytest.approx(0.0)


def test_dynamic_interval_forces_irrigation_when_max_interval_is_reached(monkeypatch, tmp_path, base_time):
    circuit = _make_circuit(threshold_percent=50, min_interval_days=1, max_interval_days=5)
    state_manager = _make_state_manager(tmp_path)
    state_manager.get_circuit_snapshot = MagicMock(return_value=_snapshot(base_time - timedelta(days=6)))

    monkeypatch.setattr("smart_irrigation_system.node.core.irrigation_circuit.time_utils.now", lambda *args, **kwargs: base_time)
    circuit.calculation_model.compute_weather_adjusted_volume.return_value = _weather_result(base_volume=100.0, final_volume=20.0)

    should_irrigate, target_volume, reason = circuit.evaluate_dynamic_interval(
        state_manager=state_manager,
        global_config=MagicMock(),
        global_conditions=MagicMock(),
    )

    assert should_irrigate is True
    assert target_volume == pytest.approx(20.0)
    assert reason is None


def test_carry_over_volume_persists_in_state_file_and_survives_reload(tmp_path):
    state_manager = _make_state_manager(tmp_path)
    state_manager.set_carry_over_volume_liters(1, 12.5)

    with open(tmp_path / "zones_state.json", "r") as f:
        raw_state = json.load(f)

    assert raw_state["circuits"][0]["carry_over_volume_liters"] == pytest.approx(12.5)

    CircuitStateManager._instance = None
    reloaded = CircuitStateManager(str(tmp_path / "zones_state.json"), str(tmp_path / "irrigation_log.json"))
    assert reloaded.get_carry_over_volume_liters(1) == pytest.approx(12.5)