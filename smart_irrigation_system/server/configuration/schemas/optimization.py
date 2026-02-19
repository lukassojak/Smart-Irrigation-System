from pydantic import BaseModel


# Request Schemas

class PlantOptimizationRequest(BaseModel):
    plant_id: str
    target_volume_liters: float
    tolerance_percent: float
    max_emitter_quantity: int

class DripperOptimizationRequest(BaseModel):
    dripper_id: str
    flow_rate_lph: float
    count: int | None = None # If None, it means unlimited availability of this dripper type

class PerPlantOptimizationRequest(BaseModel):
    plants: list[PlantOptimizationRequest]
    available_drippers: list[DripperOptimizationRequest]


# Response Schemas

class DripperAllocation(BaseModel):
    dripper_id: str
    flow_rate_lph: float
    count: int

class PlantOptimizationResult(BaseModel):
    plant_id: str
    actual_volume_liters: float
    assigned_drippers: list[DripperAllocation]

class PerPlantOptimizationResponse(BaseModel):
    plants: list[PlantOptimizationResult]
    total_drippers_used: int
    drippers_used_detail: list[DripperAllocation] # Summary of all drippers used across all plants

    total_base_volume_liters: float
    total_flow_lph: float
    base_irrigation_time_seconds: float


# Error Response Schema

class OptimizationErrorResponse(BaseModel):
    detail: str
    reason: str