from smart_irrigation_system.node.core.enums import IrrigationState

ALLOWED_TRANSITIONS = {
    IrrigationState.IDLE: {IrrigationState.IRRIGATING, IrrigationState.WAITING, IrrigationState.DISABLED},
    IrrigationState.WAITING: {IrrigationState.IRRIGATING, IrrigationState.IDLE},
    IrrigationState.IRRIGATING: {IrrigationState.IDLE},
    IrrigationState.DISABLED: {IrrigationState.IDLE},
}

def is_allowed(old: IrrigationState, new: IrrigationState) -> bool:
    allowed = ALLOWED_TRANSITIONS.get(old, set())
    return new in allowed