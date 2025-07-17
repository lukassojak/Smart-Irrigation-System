import pytest
from unittest.mock import MagicMock, patch

from smart_irrigation_system.irrigation_controller import IrrigationController
from smart_irrigation_system.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.enums import IrrigationState


@pytest.fixture
def mock_circuit():
    circuit = MagicMock(spec=IrrigationCircuit)
    circuit.id = 1
    circuit.is_irrigation_allowed.return_value = True
    circuit.get_circuit_consumption.return_value = 5.0
    circuit.irrigate_automatic.return_value = 42  # simulate irrigation duration
    return circuit


@patch("smart_irrigation_system.irrigation_controller.load_zones_config")
@patch("smart_irrigation_system.irrigation_controller.load_global_config")
@patch("smart_irrigation_system.irrigation_controller.CircuitStateManager")
@patch("smart_irrigation_system.irrigation_controller.WeatherSimulator")
def test_perform_irrigation_sequential_success(
    mock_weather, mock_state_manager, mock_load_config, mock_load_zones, mock_circuit
):
    # Arrange
    mock_global_config = MagicMock()
    mock_global_config.automation.max_flow_monitoring = False
    mock_load_config.return_value = mock_global_config

    mock_load_zones.return_value = [mock_circuit]

    mock_state_manager_instance = MagicMock()
    mock_state_manager.return_value = mock_state_manager_instance

    mock_weather_instance = MagicMock()
    mock_weather_instance.get_current_conditions.return_value = MagicMock()
    mock_weather.return_value = mock_weather_instance

    controller = IrrigationController()

    # Act
    controller.perform_irrigation_sequential()

    # Assert
    mock_circuit.is_irrigation_allowed.assert_called_once()
    mock_circuit.irrigate_automatic.assert_called_once()
    mock_state_manager_instance.update_irrigation_result.assert_called_with(mock_circuit, "success", 42)
    assert mock_circuit.state == IrrigationState.IDLE


def test_perform_irrigation_sequential_skip(mock_circuit):
    # Arrange
    mock_circuit.is_irrigation_allowed.return_value = False

    controller = IrrigationController()
    controller.circuits = {mock_circuit.id: mock_circuit}

    # Act
    controller.perform_irrigation_sequential()

    # Assert
    mock_circuit.is_irrigation_allowed.assert_called_once()
    mock_circuit.irrigate_automatic.assert_not_called()
    # assert mock_circuit.state == IrrigationState.IDLE


def test_perform_irrigation_sequential_error(mock_circuit):
    # Arrange
    mock_circuit.is_irrigation_allowed.return_value = True
    mock_circuit.irrigate_automatic.side_effect = Exception("Irrigation error")

    controller = IrrigationController()
    controller.circuits = {mock_circuit.id: mock_circuit}

    # Act
    controller.perform_irrigation_sequential()

    # Assert
    mock_circuit.is_irrigation_allowed.assert_called_once()
    mock_circuit.irrigate_automatic.assert_called_once()
    assert mock_circuit.state == IrrigationState.IDLE


def test_stop_irrigation(mock_circuit):
    # Arrange
    controller = IrrigationController()
    controller.circuits = {mock_circuit.id: mock_circuit}
    controller.stop_event.clear()

    # Act
    controller.stop_irrigation()

    # Assert
    assert controller.stop_event.is_set()
    mock_circuit.state = IrrigationState.IDLE  # Ensure state is reset
    assert mock_circuit.state == IrrigationState.IDLE


def test_perform_irrigation_sequential_max_flow(mock_circuit):
    # Arrange
    mock_global_config = MagicMock()
    mock_global_config.automation.max_flow_monitoring = True
    mock_global_config.irrigation_limits.main_valve_max_flow = 10.0

    mock_circuit.get_circuit_consumption.return_value = 15.0  # Exceeds max flow limit

    controller = IrrigationController()
    controller.global_config = mock_global_config
    controller.circuits = {mock_circuit.id: mock_circuit}

    # Act
    controller.perform_irrigation_sequential()

    # Assert
    mock_circuit.is_irrigation_allowed.assert_called_once()
    mock_circuit.irrigate_automatic.assert_not_called()  # Should not irrigate due to high consumption
