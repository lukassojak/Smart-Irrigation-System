from pydantic import BaseModel


class InputPins(BaseModel):
    pins: list[int]

class OutputPins(BaseModel):
    pins: list[int]

class HardwareConfiguration(BaseModel):
    input_pins: InputPins
    output_pins: OutputPins