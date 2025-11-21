# smart_irrigation_system/server/api/routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from smart_irrigation_system.server.core.server_core import IrrigationServer


router = APIRouter()
server = IrrigationServer()

# ===========================================================================================================
# Data models
# ===========================================================================================================

class StartIrrigationRequest(BaseModel):
    zone_id: int = Field(..., description="ID of the irrigation zone to start")
    liter_amount: float = Field(..., description="Amount of water in liters to irrigate")

class NodeRequest(BaseModel):
    node_id: str = Field(..., description="Unique identifier of the target irrigation node")


# ============================================================================================================
# api endpoints
# ============================================================================================================

@router.get("/")
def root() -> dict:
    """Root endpoint."""
    return {"message": "Server REST API is running."}


@router.get("/nodes")
def get_nodes() -> dict:
    """Endpoint to get the list of registered irrigation nodes with parsed status."""
    try:
        nodes = server.get_node_summary()

        return {"nodes": nodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nodes: {str(e)}")


@router.post("/update_status")
def update_status() -> dict:
    """Endpoint to update status summary of all nodes (sends MQTT commands)."""
    try:
        server.update_all_node_statuses()
        return {"message": f"Status update requests sent to all nodes."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send status update requests: {str(e)}")


@router.post("/start_irrigation")
def start_irrigation(req: StartIrrigationRequest) -> dict:
    """Endpoint to start irrigation on a specific zone (sends MQTT command)."""
    try:
        command = {
            "action": "start_irrigation",
            "zone_id": req.zone_id,
            "liter_amount": req.liter_amount
        }
        node_id = server.zone_node_mapper.get_node_for_zone(req.zone_id)
        server.mqtt_manager.publish_command(node_id, command)
        return {"message": f"Irrigation command sent for zone {req.zone_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send irrigation command: {str(e)}")


@router.post("/stop_irrigation")
def stop_irrigation() -> dict:
    """Endpoint to stop irrigation on all nodes (sends MQTT command)."""
    try:
        server.stop_all_irrigation()
        return {"message": f"Stop irrigation command sent to all nodes."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send stop irrigation command: {str(e)}")
    

@router.get("/ping")
def ping() -> dict:
    """Health check endpoint."""
    return {"message": "pong"}
