from fastapi import APIRouter, HTTPException
from smart_irrigation_system.server.runtime.services.live_service import get_live_snapshot, get_discovered_devices, get_nodes_snapshot, get_node_detail
from smart_irrigation_system.server.runtime.services.today_service import get_today_snapshot
from smart_irrigation_system.server.runtime.schemas.live import LiveResponse, NodeLive, NodeDetail
from smart_irrigation_system.server.runtime.schemas.today import TodayResponse
from smart_irrigation_system.server.runtime.schemas.discovery import DiscoveredDeviceRead

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


@router.get(
    "/discovered",
    summary="List discovered devices",
    response_model=list[DiscoveredDeviceRead],
    status_code=200
)
def discovered_devices():
    return get_discovered_devices()


@router.get(
    "/nodes",
    summary="List runtime nodes",
    response_model=list[NodeLive],
    status_code=200,
)
def nodes():
    return get_nodes_snapshot()


@router.get(
    "/nodes/{node_id}",
    summary="Get node detail",
    response_model=NodeDetail,
    status_code=200,
)
def node_detail(node_id: int):
    detail = get_node_detail(node_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return detail