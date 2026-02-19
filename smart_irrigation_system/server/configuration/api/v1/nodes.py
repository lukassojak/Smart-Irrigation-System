from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from smart_irrigation_system.server.configuration.schemas.node import NodeCreate, NodeRead, NodeListRead
from smart_irrigation_system.server.configuration.schemas.zone import ZoneCreate, ZoneRead, ZoneListRead
from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.services.node_service import NodeService
from smart_irrigation_system.server.db.session import get_session
from smart_irrigation_system.server.configuration.exporters.node_config_exporter import export_node_config

router = APIRouter()


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