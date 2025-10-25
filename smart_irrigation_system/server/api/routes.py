# smart_irrigation_system/server/api/routes.py
from fastapi import APIRouter
from pydantic import BaseModel, Field
from smart_irrigation_system.server.core.server_core import IrrigationServer

router = APIRouter()
server = IrrigationServer() # Singleton instance


# ------------------- Data Models ------------------- #
class StartIrrigationRequest(BaseModel):
    zone_id: int = Field(..., description="ID of the irrigation zone to start")
    liter_amount: float = Field(..., description="Amount of water in liters to irrigate")

class NodeRequest(BaseModel):
    node_id: str = Field(..., description="Unique identifier of the target irrigation node")


# ------------------- API Endpoints ------------------- #
@router.get("/")
def root():
    """Root endpoint."""
    return {"message": "Smart Irrigation Server REST API is running."}

@router.get("/nodes")
def get_nodes():
    """Endpoint to get the list of registered irrigation nodes."""
    try:
        nodes = server.get_node_summary()
        return {"nodes": nodes}
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve nodes: {str(e)}")

@router.post("/get_status")
def get_status(req: NodeRequest):
    """Endpoint to get status summary of a specific irrigation node (sends MQTT command)."""
    try:
        command = {"action": "get_status"}
        server.mqtt_manager.publish_command(req.node_id, command)
        return {"message": f"Status request sent to node {req.node_id}."}
    except Exception as e:
        raise RuntimeError(f"Failed to send status request: {str(e)}")

@router.post("/start_irrigation")
def start_irrigation(req: StartIrrigationRequest):
    """Endpoint to start irrigation on a specific zone (sends MQTT command)."""
    try:
        command = {
            "action": "start_irrigation",
            "zone_id": req.zone_id,
            "liter_amount": req.liter_amount
        }
        server.mqtt_manager.publish_command("node1", command)   # TODO: Make node ID dynamic - use node registry to find appropriate node / NodeManager
        return {"message": f"Irrigation command sent for zone {req.zone_id}."}
    except Exception as e:
        raise RuntimeError(f"Failed to send irrigation command: {str(e)}")

@router.post("/stop_irrigation")
def stop_irrigation(req: NodeRequest):
    """Endpoint to stop irrigation on a specific node (sends MQTT command)."""
    try:
        command = {"action": "stop_irrigation"}
        server.mqtt_manager.publish_command(req.node_id, command)
        return {"message": f"Stop irrigation command sent to node {req.node_id}."}
    except Exception as e:
        raise RuntimeError(f"Failed to send stop irrigation command: {str(e)}")
    
@router.get("/ping")
def ping():
    """Health check endpoint."""
    return {"message": "pong"}
