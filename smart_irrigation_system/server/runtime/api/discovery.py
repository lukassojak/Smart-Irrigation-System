import time

from fastapi import APIRouter, HTTPException, Query

from smart_irrigation_system.server.runtime.schemas.discovery import DiscoveredDeviceRead
from smart_irrigation_system.server.runtime.services.live_service import get_discovered_devices, get_live_store


router = APIRouter()


@router.get(
    "/devices",
    summary="List discovered unassigned devices",
    response_model=list[DiscoveredDeviceRead],
    status_code=200,
)
def list_discovered_devices() -> list[DiscoveredDeviceRead]:
    return get_discovered_devices()


@router.post(
    "/devices/{hardware_uid}/pair",
    summary="Wait for live discovery response from selected device",
    response_model=dict,
    status_code=200,
)
def pair_discovered_device(
    hardware_uid: str,
    min_wait_seconds: float = Query(2.0, ge=0.0, le=10.0),
    timeout_seconds: float = Query(8.0, ge=1.0, le=30.0),
) -> dict:
    store = get_live_store()
    devices = {d.hardware_uid: d for d in store.list_discovered_devices()}
    baseline = devices.get(hardware_uid)
    if baseline is None:
        raise HTTPException(status_code=404, detail=f"Device '{hardware_uid}' is not available in discovery list.")

    baseline_seen_at = baseline.last_seen_at
    started = time.monotonic()
    deadline = started + timeout_seconds

    while time.monotonic() < deadline:
        current = {d.hardware_uid: d for d in store.list_discovered_devices()}.get(hardware_uid)
        if current and current.last_seen_at and (baseline_seen_at is None or current.last_seen_at > baseline_seen_at):
            elapsed = time.monotonic() - started
            remaining_min_wait = max(min_wait_seconds - elapsed, 0.0)
            if remaining_min_wait > 0:
                time.sleep(remaining_min_wait)

            return {
                "status": "READY",
                "hardware_uid": current.hardware_uid,
                "serial_number": current.serial_number,
                "hostname": current.hostname,
                "last_seen_at": current.last_seen_at,
            }

        time.sleep(0.2)

    raise HTTPException(
        status_code=504,
        detail=(
            "Selected device did not send a new discovery HELLO in time. "
            "Make sure the node is online and retry."
        ),
    )