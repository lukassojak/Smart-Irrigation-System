from fastapi import APIRouter
from smart_irrigation_system.server.runtime.services.live_service import get_live_snapshot
from smart_irrigation_system.server.runtime.schemas.live import LiveResponse


router = APIRouter()


@router.get(
    "/live",
    summary="Get live status snapshot",
    response_model=LiveResponse,
    status_code=200
)
def live():
    return get_live_snapshot()