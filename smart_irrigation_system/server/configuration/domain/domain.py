from enum import Enum


class IrrigationMode(str, Enum):
    EVEN_AREA = "even_area"
    PER_PLANT = "per_plant"