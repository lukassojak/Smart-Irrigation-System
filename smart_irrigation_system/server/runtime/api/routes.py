from fastapi import APIRouter
from .control import router as control_router
from .discovery import router as discovery_router
from .statuses import router as statuses_router
from .history import router as history_router


router = APIRouter()
router.include_router(
    history_router,
    prefix="/history",
    tags=["history"]
)
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
router.include_router(
    discovery_router,
    prefix="/discovery",
    tags=["discovery"]
)

