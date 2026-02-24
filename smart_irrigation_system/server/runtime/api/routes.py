from fastapi import APIRouter, HTTPException
from smart_irrigation_system.server.runtime.services.live_service import get_live_snapshot
from smart_irrigation_system.server.runtime.services.today_service import get_today_snapshot
from smart_irrigation_system.server.runtime.schemas.live import LiveResponse
from smart_irrigation_system.server.runtime.schemas.today import TodayResponse


router = APIRouter()


@router.get(
    "/live",
    summary="Get live status snapshot",
    response_model=LiveResponse,
    status_code=200
)
def live():
    return get_live_snapshot()

@router.get(
    "/today",
    summary="Get today's irrigation scheduled tasks",
    response_model=TodayResponse,
    status_code=200
)
def today():
    return get_today_snapshot()