import pytest
from unittest.mock import MagicMock, patch

from smart_irrigation_system.node.core.relay_valve import RelayValve
from smart_irrigation_system.node.core.enums import RelayValveState
from smart_irrigation_system.node.exceptions import (
    RelayValveStateError,
    GPIOInitializationError,
    GPIOWriteError,
)



# ---------------------- Tests ----------------------

# NOTE: RelayValve._gpio_initialized is a class variable, so it retains its value across tests.


def test_closed_state_on_init():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        # Act
        relay_valve = RelayValve(pin=17)

        # Assert
        assert relay_valve.state == RelayValveState.CLOSED
        mock_gpio.output.assert_called_once_with(17, mock_gpio.HIGH)


def test_open_valve_changes_state_to_open():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(pin=17)

        # Act
        relay_valve.set_state(RelayValveState.OPEN)

        # Assert
        assert relay_valve.state == RelayValveState.OPEN
        mock_gpio.output.assert_called_with(17, mock_gpio.LOW) # Last call should set pin to LOW to open valve


def test_close_valve_changes_state_to_closed():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(pin=17)

        # Act
        relay_valve.set_state(RelayValveState.OPEN)
        relay_valve.set_state(RelayValveState.CLOSED)

        # Assert
        assert relay_valve.state == RelayValveState.CLOSED
        mock_gpio.output.assert_called_with(17, mock_gpio.HIGH)


def test_open_valve_state_and_gpio_are_consistent():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(17)

        # Act
        relay_valve.set_state(RelayValveState.OPEN)

        # Assert
        assert relay_valve.state == RelayValveState.OPEN
        mock_gpio.output.assert_called_with(17, mock_gpio.LOW)


def test_open_valve_twice_does_not_change_state():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(17)

        # Act
        relay_valve.set_state(RelayValveState.OPEN)
        relay_valve.set_state(RelayValveState.OPEN)

        # Assert
        assert relay_valve.state == RelayValveState.OPEN


def test_open_valve_twice_does_not_cause_gpio_write():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(17)
        mock_gpio.output.reset_mock()

        # Act
        relay_valve.set_state(RelayValveState.OPEN)
        relay_valve.set_state(RelayValveState.OPEN)

        # Assert
        mock_gpio.output.assert_called_once_with(17, mock_gpio.LOW)

    
def test_close_valve_twice_does_not_change_state():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(17)
        relay_valve.set_state(RelayValveState.OPEN)

        # Act
        relay_valve.set_state(RelayValveState.CLOSED)
        relay_valve.set_state(RelayValveState.CLOSED)

        # Assert
        assert relay_valve.state == RelayValveState.CLOSED


def test_close_valve_twice_does_not_cause_gpio_write():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(17)
        relay_valve.set_state(RelayValveState.OPEN)
        mock_gpio.output.reset_mock()

        # Act
        relay_valve.set_state(RelayValveState.CLOSED)
        relay_valve.set_state(RelayValveState.CLOSED)

        # Assert
        mock_gpio.output.assert_called_once_with(17, mock_gpio.HIGH)


def test_raises_exception_on_gpio_failure_during_open():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(17)
        mock_gpio.output.side_effect = GPIOWriteError("GPIO write failed")

        # Act & Assert
        with pytest.raises(RelayValveStateError):
            relay_valve.set_state(RelayValveState.OPEN, retry=1)
        

def test_raises_exception_on_gpio_failure_during_close():
    # Arrange
    with patch("smart_irrigation_system.node.core.relay_valve.GPIO") as mock_gpio:
        relay_valve = RelayValve(17)
        relay_valve.set_state(RelayValveState.OPEN)

        mock_gpio.output.side_effect = GPIOWriteError("GPIO write failed")

        # Act & Assert
        with pytest.raises(RelayValveStateError):
            relay_valve.set_state(RelayValveState.CLOSED, retry=1)
    