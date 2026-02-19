from fastapi import APIRouter
from .nodes import router as nodes_router
from .optimization import router as optimization_router

router = APIRouter()
router.include_router(nodes_router, prefix="/nodes", tags=["nodes"])
router.include_router(optimization_router, prefix="/optimization", tags=["optimization"])