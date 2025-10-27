# smart_irrigation_system/server/api/routes.py
from fastapi import APIRouter
from pydantic import BaseModel, Field
from smart_irrigation_system.server.core.server_core import IrrigationServer
from smart_irrigation_system.server.core.node_registry import parse_node_status


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
    """Endpoint to get the list of registered irrigation nodes with parsed status."""
    try:
        nodes = server.get_node_summary()
        parsed_nodes = {}

        for node_id, data in nodes.items():
            raw_status = data.get("last_status")
            parsed_nodes[node_id] = {
                **data,
                "status": parse_node_status(raw_status)
            }

        return {"nodes": parsed_nodes}
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve nodes: {str(e)}")

@router.post("/update_status")
def update_status():
    """Endpoint to update status summary of all nodes (sends MQTT commands)."""
    try:
        command = {"action": "get_status"}
        server.update_all_node_statuses()
        return {"message": f"Status update requests sent to all nodes."}
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
        node_id = server.zone_node_mapper.get_node_for_zone(req.zone_id)
        server.mqtt_manager.publish_command(node_id, command)
        return {"message": f"Irrigation command sent for zone {req.zone_id}."}
    except Exception as e:
        raise RuntimeError(f"Failed to send irrigation command: {str(e)}")

@router.post("/stop_irrigation")
def stop_irrigation():
    """Endpoint to stop irrigation on all nodes (sends MQTT command)."""
    try:
        command = {"action": "stop_irrigation"}
        server.stop_all_irrigation()
        return {"message": f"Stop irrigation command sent to all nodes."}
    except Exception as e:
        raise RuntimeError(f"Failed to send stop irrigation command: {str(e)}")
    
@router.get("/ping")
def ping():
    """Health check endpoint."""
    return {"message": "pong"}
