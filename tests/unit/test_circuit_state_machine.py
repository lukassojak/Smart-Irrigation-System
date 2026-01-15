import pytest

from smart_irrigation_system.node.core.circuit_state_machine import is_allowed
from smart_irrigation_system.node.core.enums import IrrigationState

# ---------------------- Mocks/Fakes ----------------------

# ---------------------- Fixtures ----------------------

# ---------------------- Tests ----------------------

@pytest.mark.parametrize(
        "from_state, to_state",
        [
            (IrrigationState.IDLE, IrrigationState.IRRIGATING),
            (IrrigationState.IDLE, IrrigationState.WAITING),
            (IrrigationState.IDLE, IrrigationState.DISABLED),
            (IrrigationState.IRRIGATING, IrrigationState.IDLE),
            (IrrigationState.WAITING, IrrigationState.IDLE),
            (IrrigationState.WAITING, IrrigationState.IRRIGATING),
            (IrrigationState.DISABLED, IrrigationState.IDLE)
        ]
)
def test_transition_is_allowed(from_state, to_state):
    assert is_allowed(old=from_state, new=to_state)


@pytest.mark.parametrize(
        "from_state, to_state",
        [
            (IrrigationState.IRRIGATING, IrrigationState.WAITING),
            (IrrigationState.IRRIGATING, IrrigationState.DISABLED),
            (IrrigationState.WAITING, IrrigationState.DISABLED),
            (IrrigationState.DISABLED, IrrigationState.IRRIGATING),
            (IrrigationState.DISABLED, IrrigationState.WAITING)
        ]
)
def test_transition_is_not_allowed(from_state, to_state):
    assert not is_allowed(old=from_state, new=to_state)