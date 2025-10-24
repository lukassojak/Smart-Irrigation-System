import pytest
from unittest.mock import MagicMock, patch
from smart_irrigation_system.node.core.relay_valve import RelayValve


def test_control_open_prints_open_message():
    valve = RelayValve(pin=5)
    with patch("builtins.print") as mock_print:
        valve.control(True)
        mock_print.assert_called_with("Valve      5: OPEN-VALVE ")


def test_control_close_prints_close_message():
    valve = RelayValve(pin=5)
    with patch("builtins.print") as mock_print:
        valve.control(False)
        mock_print.assert_called_with("Valve      5: CLOSE-VALVE ")


def test_open_valve_normal_duration():
    valve = RelayValve(pin=7)
    mock_stop_event = MagicMock()
    mock_stop_event.wait.return_value = False  # simulate waiting full duration

    with patch("builtins.print") as mock_print:
        valve.open(duration=3, stop_event=mock_stop_event)

        mock_print.assert_any_call("Valve      7: valve will be opened for 3 seconds")
        mock_print.assert_any_call("Valve      7: Closing valve duly after 3 seconds")
        mock_print.assert_any_call("Valve      7: OPEN-VALVE ")
        mock_print.assert_any_call("Valve      7: CLOSE-VALVE ")


def test_open_valve_early_stop():
    valve = RelayValve(pin=8)
    mock_stop_event = MagicMock()
    mock_stop_event.wait.return_value = True  # simulate early stop

    with patch("builtins.print") as mock_print:
        valve.open(duration=10, stop_event=mock_stop_event)

        mock_print.assert_any_call("Valve      8: valve will be opened for 10 seconds")
        mock_print.assert_any_call("Valve      8: Closing valve early.")
        mock_print.assert_any_call("Valve      8: OPEN-VALVE ")
        mock_print.assert_any_call("Valve      8: CLOSE-VALVE ")
