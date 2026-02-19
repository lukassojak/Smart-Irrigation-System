from pydantic import BaseModel
from enum import Enum


# ---- Enums ----

class EmitterType(str, Enum):
    DRIPPER = "dripper"
    SPRINKLER = "sprinkler"
    MICRO_SPRAY = "micro_spray"
    SOAKER_HOSE = "soaker_hose"


# ---- Emitters Schemas ----

class Emitter(BaseModel):
    type: EmitterType
    flow_rate_lph: float
    count: int

class Plant(BaseModel):
    id: str
    name: str
    emitters: list[Emitter]

class EmittersConfigurationEvenArea(BaseModel):
    summary: list[Emitter]

class EmittersConfigurationPerPlant(BaseModel):
    plants: list[Plant]