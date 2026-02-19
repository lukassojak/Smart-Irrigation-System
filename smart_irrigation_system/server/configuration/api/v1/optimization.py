from fastapi import APIRouter, HTTPException

from smart_irrigation_system.server.configuration.optimization.per_plant_optimizer import PerPlantOptimizer, NoSolutionException, InfeasibleSolutionException
from smart_irrigation_system.server.configuration.schemas.optimization import (
    PerPlantOptimizationRequest,
    PerPlantOptimizationResponse,
    OptimizationErrorResponse
)

router = APIRouter()
print("Optimization router initialized")


# ----- Optimization Endpoints -----

@router.post(
    "/per-plant",
    summary="Optimize dripper allocation for plants",
    response_model=PerPlantOptimizationResponse,
    status_code=200,
)
def optimize_drippers(data: PerPlantOptimizationRequest):
    optimizer = PerPlantOptimizer(data)

    try:
        response = optimizer.optimize()
    except NoSolutionException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InfeasibleSolutionException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=400, detail="Optimization timed out")
    
    return response

    