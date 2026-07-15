from fastapi import APIRouter
from .irrigation_history import router as irrigation_history_router

router = APIRouter()

router.include_router(
    irrigation_history_router,
    prefix="/irrigation-history",
    tags=["irrigation-history"]
)