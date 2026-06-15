from fastapi import APIRouter, HTTPException

from smart_irrigation_system.__version__ import __version__
from smart_irrigation_system.server.runtime.schemas.live import NodeMetadata
from smart_irrigation_system.server.runtime.services.live_service import get_node_metadata as get_node_metadata_service

router = APIRouter()

@router.get(
    "/version",
    summary="Get server version",
    response_model=dict,
)
def get_version():
    try:
        return {"version": __version__}
    except Exception as e:
        return {"error": str(e)}

@router.get(
    "/nodes/{node_id}/metadata",
    summary="Get metadata for a specific node",
    response_model=NodeMetadata,
)
def get_node_metadata(node_id: int):
        try:
            metadata = get_node_metadata_service(node_id=node_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        if metadata is None:
            raise HTTPException(status_code=404, detail="Node metadata not found")
        return metadata
