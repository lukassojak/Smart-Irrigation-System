from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from smart_irrigation_system.server.configuration.schemas.node import NodeCreate, NodeRead, NodeListRead, NodeUpdate
from smart_irrigation_system.server.configuration.schemas.zone import ZoneCreate, ZoneRead, ZoneListRead, ZoneUpdate
from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.services.node_service import NodeService
from smart_irrigation_system.server.db.session import get_session
from smart_irrigation_system.server.configuration.exporters.node_config_exporter import (
    export_node_config,
    export_node_legacy_runtime_config,
)
from smart_irrigation_system.server.runtime.services.live_service import initialize_live_store_from_config

router = APIRouter()


def _sync_runtime_topology(session: Session) -> None:
    """Refresh in-memory runtime topology after config DB mutations."""
    initialize_live_store_from_config(session)


# ----- CRUD Operations for Node -----

@router.post(
    "/",
    summary="Create node",
    response_model=NodeRead,
    status_code=201,
)
def create_node(data: NodeCreate, session: Session = Depends(get_session)):
    service = NodeService(session)
    node = service.create_node(data)
    _sync_runtime_topology(session)
    return NodeRead.model_validate(node)


@router.get(
    "/",
    summary="List nodes",
    response_model=list[NodeListRead],
    status_code=200,
)
def list_nodes(session: Session = Depends(get_session)):
    service = NodeService(session)
    nodes: list[Node] = service.list_nodes()
    list_read_nodes = [NodeListRead.model_validate(n) for n in nodes]
    return list_read_nodes


@router.get(
    "/{node_id}",
    summary="Get node by ID",
    response_model=NodeRead,
    status_code=200,
)
def get_node(node_id: int, session: Session = Depends(get_session)):
    service = NodeService(session)
    node = service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodeRead.model_validate(node)


@router.patch(
    "/{node_id}",
    summary="Update node by ID",
    response_model=NodeRead,
    status_code=200,
)
def update_node(node_id: int, data: NodeUpdate, session: Session = Depends(get_session)):
    service = NodeService(session)
    node = service.update_node(node_id, data)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    _sync_runtime_topology(session)
    return NodeRead.model_validate(node)


@router.delete(
    "/{node_id}",
    summary="Delete node by ID",
    status_code=204,
)
def delete_node(node_id: int, session: Session = Depends(get_session)):
    service = NodeService(session)
    success = service.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    _sync_runtime_topology(session)


# ----- CRUD Operations for Zone -----

@router.post(
    "/{node_id}/zones",
    summary="Create zone for a node",
    response_model=ZoneRead,
    status_code=201,
)
def create_zone(node_id: int, data: ZoneCreate, session: Session = Depends(get_session)):
    service = NodeService(session)
    try:
        zone: Zone = service.add_zone_to_node(node_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    _sync_runtime_topology(session)
    return ZoneRead.model_validate(zone)


@router.get(
    "/{node_id}/zones",
    summary="List zones for a node",
    response_model=list[ZoneListRead],
    status_code=200,
)
def list_zones(node_id: int, session: Session = Depends(get_session)):
    service = NodeService(session)
    zones: list[Zone] = service.list_zones(node_id)
    list_read_zones = [ZoneListRead.model_validate(z) for z in zones]
    return list_read_zones


@router.get(
    "/{node_id}/zones/{zone_id}",
    summary="Get zone by ID for a node",
    response_model=ZoneRead,
    status_code=200,
)
def get_zone(node_id: int, zone_id: int, session: Session = Depends(get_session)):
    service = NodeService(session)
    zone: Zone = service.get_zone(node_id, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return ZoneRead.model_validate(zone)


@router.patch(
    "/{node_id}/zones/{zone_id}",
    summary="Update zone by ID for a node",
    response_model=ZoneRead,
    status_code=200,
)
def update_zone(node_id: int, zone_id: int, data: ZoneUpdate, session: Session = Depends(get_session)):
    service = NodeService(session)
    zone = service.update_zone(node_id, zone_id, data)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    _sync_runtime_topology(session)
    return ZoneRead.model_validate(zone)


@router.delete(
    "/{node_id}/zones/{zone_id}",
    summary="Delete zone by ID for a node",
    status_code=204,
)
def delete_zone(node_id: int, zone_id: int, session: Session = Depends(get_session)):
    service = NodeService(session)
    success = service.delete_zone(node_id, zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zone not found")
    _sync_runtime_topology(session)
    

@router.get(
    "/{node_id}/export",
    summary="Export node configuration",
    response_model=dict,
    status_code=200,
)
def export_node(node_id: int, session: Session = Depends(get_session)):
    service = NodeService(session)
    node = service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    config = export_node_config(node)
    return config


@router.get(
    "/{node_id}/export/legacy-runtime",
    summary="Export node configuration in current node runtime file format",
    response_model=dict,
    status_code=200,
)
def export_node_legacy_runtime(node_id: int, session: Session = Depends(get_session)):
    service = NodeService(session)
    node = service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    return export_node_legacy_runtime_config(node)