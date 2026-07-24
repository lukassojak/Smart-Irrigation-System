from fastapi import APIRouter
from .irrigation_history import router as irrigation_history_router
from .statistics import router as statistics_router

router = APIRouter()

router.include_router(
    irrigation_history_router,
    prefix="/irrigation-history",
    tags=["irrigation-history"]
)
router.include_router(
    statistics_router,
    prefix="/statistics",
    tags=["statistics"]
)