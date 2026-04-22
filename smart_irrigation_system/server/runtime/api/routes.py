from fastapi import APIRouter
from .control import router as control_router
from .statuses import router as statuses_router


router = APIRouter()
router.include_router(
    statuses_router,
    prefix="/statuses",
    tags=["statuses"]
)
router.include_router(
    control_router,
    prefix="/control",
    tags=["control"]
)

