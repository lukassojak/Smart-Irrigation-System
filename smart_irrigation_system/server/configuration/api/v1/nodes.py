from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from sqlmodel import Session

from smart_irrigation_system.server.configuration.schemas.node import NodeCreate, NodeRead, NodeListRead, NodeUpdate
from smart_irrigation_system.server.configuration.schemas.zone import ZoneCreate, ZoneRead, ZoneListRead, ZoneUpdate
from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.models.node import CONFIG_SYNC_PENDING
from smart_irrigation_system.server.configuration.services.node_service import NodeService
from smart_irrigation_system.server.configuration.services.global_config_service import GlobalConfigService
from smart_irrigation_system.server.db.session import get_session
from smart_irrigation_system.server.configuration.exporters.node_config_exporter import (
    export_node_config,
    export_node_legacy_runtime_config,
)
from smart_irrigation_system.server.runtime.services.live_service import initialize_live_store_from_config
from smart_irrigation_system.server.core.server_core import IrrigationServer
from smart_irrigation_system.common.mqtt_contract import ApplyMode, MessageType

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
    server = IrrigationServer()

    session.commit()
    _sync_runtime_topology(session)

    try:
        if node.hardware_uid:
            response = server.mqtt_manager.publish_assign_node_id_and_wait(
                hardware_uid=node.hardware_uid,
                assigned_node_id=str(node.id),
                node_name=node.name,
                timeout=5,
            )

            if response.get("message_type") != MessageType.NODE_ASSIGNMENT_ACK.value:
                raise HTTPException(status_code=502, detail={"message": "Unexpected assignment response", "response": response})

            response_uid = response.get("payload", {}).get("assigned_node_id")
            if str(response_uid) != str(node.id):
                raise HTTPException(
                    status_code=502,
                    detail={"message": "Assignment ACK returned mismatched node id", "response": response},
                )

            server.mqtt_manager.live_store.claim_discovered_device(node.hardware_uid, node.id)

        return NodeRead.model_validate(node)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Device did not acknowledge node assignment within 5 seconds.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to provision node: {str(exc)}")


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
    node = service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    server = IrrigationServer()
    if node.hardware_uid:
        # First: attempt to push an updated (empty) runtime config to the node
        # so that the node will remove any configured zones before we unpair it.
        try:
            global_config = GlobalConfigService(session).get_or_create()
            legacy_runtime_config = export_node_legacy_runtime_config(node, global_config)
            # Clear zones in the runtime config so node will remove them
            if isinstance(legacy_runtime_config, dict):
                legacy_runtime_config["zones"] = []

            try:
                response = server.mqtt_manager.publish_apply_config_and_wait(
                    node_id=str(node.id),
                    config_revision=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                    legacy_runtime_config=legacy_runtime_config,
                    apply_mode=ApplyMode.APPLY_NOW,
                    requested_by="configuration-api-delete-node",
                    timeout=5,
                )

                if response.get("message_type") == "NODE_ACK" and response.get("payload", {}).get("ack_type") == "applied":
                    # mark pushed so server-side state stays consistent
                    service.mark_config_pushed(node.id)
                # ignore other responses and proceed to unpair; unpair may still succeed
            except TimeoutError:
                # No ACK from node - reject delete
                raise HTTPException(
                    status_code=504,
                    detail="Node did not acknowledge config apply within 5 seconds. Delete was cancelled.",
                )
            except Exception:
                raise HTTPException(status_code=503, detail="Failed to push config to node before delete. Delete was cancelled.")
        except Exception:
            # Reject delete if attempt to prepare node for deletion fails
            raise HTTPException(status_code=503, detail="Failed to prepare node for deletion. Delete was cancelled.")

        # Now unpair the node
        try:
            response = server.mqtt_manager.publish_unpair_node_and_wait(
                node_id=str(node.id),
                hardware_uid=node.hardware_uid,
                timeout=5,
            )
        except TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Node did not acknowledge unpair within 5 seconds. Delete was cancelled.",
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Failed to unpair node before delete: {str(exc)}")

        if response.get("message_type") != MessageType.NODE_UNPAIR_ACK.value:
            raise HTTPException(
                status_code=502,
                detail={"message": "Unexpected unpair response", "response": response},
            )

        response_uid = str(response.get("payload", {}).get("hardware_uid") or "")
        if response_uid and response_uid != node.hardware_uid:
            raise HTTPException(
                status_code=502,
                detail={"message": "Unpair ACK returned mismatched hardware UID", "response": response},
            )

    success = service.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.hardware_uid:
        server.mqtt_manager.live_store.unclaim_discovered_device(node.hardware_uid)

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
    # fetch node to know whether we should push updated config to device
    node = service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    success = service.delete_zone(node_id, zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Push updated runtime config to node so it removes the zone from its local config
    if node.hardware_uid:
        server = IrrigationServer()
        try:
            global_config = GlobalConfigService(session).get_or_create()
            legacy_runtime_config = export_node_legacy_runtime_config(node, global_config)
            try:
                response = server.mqtt_manager.publish_apply_config_and_wait(
                    node_id=str(node.id),
                    config_revision=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                    legacy_runtime_config=legacy_runtime_config,
                    apply_mode=ApplyMode.APPLY_NOW,
                    requested_by="configuration-api-delete-zone",
                    timeout=5,
                )

                if response.get("message_type") == "NODE_ACK" and response.get("payload", {}).get("ack_type") == "applied":
                    service.mark_config_pushed(node.id)
            except TimeoutError:
                # Proceed; even if node doesn't ACK, server-side deletion succeeded
                pass
            except Exception:
                pass
        except Exception:
            pass

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

    global_config = GlobalConfigService(session).get_or_create()
    return export_node_legacy_runtime_config(node, global_config)


@router.post(
    "/{node_id}/push-config",
    summary="Push node configuration over MQTT using v1 contract",
    response_model=dict,
    status_code=200,
)
def push_node_config(node_id: int, session: Session = Depends(get_session)):
    service = NodeService(session)
    node = service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    global_config = GlobalConfigService(session).get_or_create()
    legacy_runtime_config = export_node_legacy_runtime_config(node, global_config)
    server = IrrigationServer()
    
    try:
        response = server.mqtt_manager.publish_apply_config_and_wait(
            node_id=str(node_id),
            config_revision=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            legacy_runtime_config=legacy_runtime_config,
            apply_mode=ApplyMode.APPLY_NOW,
            requested_by="configuration-api",
            timeout=5,  # 5 second timeout for node response
        )
        
        # Check response type
        if response["message_type"] == "NODE_ACK":
            ack_type = response["payload"].get("ack_type")
            if ack_type != "applied":
                raise HTTPException(
                    status_code=502,
                    detail=f"Unexpected ACK type for config apply: {ack_type}",
                )

            service.mark_config_pushed(node_id)
            # Sync runtime topology to ensure any changes from the new config are reflected in-memory
            _sync_runtime_topology(session)
            return {
                "status": "APPLIED",
                "message": "Configuration applied successfully.",
                "ack_type": ack_type,
            }
        elif response["message_type"] == "NODE_ERROR":
            error_code = response["payload"].get("code")
            error_message = response["payload"].get("message")
            error_retryable = response["payload"].get("retryable", False)
            
            # Return 400 for non-retryable errors, 409 for retryable (conflict)
            status_code = 409 if error_retryable else 400
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error_code": error_code,
                    "message": error_message,
                    "retryable": error_retryable,
                },
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected response type: {response['message_type']}"
            )
            
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Node did not respond within 5 seconds. The node may be offline or busy."
        )


@router.post(
    "/push-config-all",
    summary="Push configuration to all nodes with pending sync status",
    response_model=dict,
    status_code=200,
)
def push_all_pending_node_configs(session: Session = Depends(get_session)):
    service = NodeService(session)
    global_config = GlobalConfigService(session).get_or_create()
    server = IrrigationServer()

    nodes = service.list_nodes()
    pending_nodes = [node for node in nodes if node.config_sync_status == CONFIG_SYNC_PENDING]

    results: list[dict] = []
    success_count = 0

    for node in pending_nodes:
        legacy_runtime_config = export_node_legacy_runtime_config(node, global_config)
        try:
            response = server.mqtt_manager.publish_apply_config_and_wait(
                node_id=str(node.id),
                config_revision=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                legacy_runtime_config=legacy_runtime_config,
                apply_mode=ApplyMode.APPLY_NOW,
                requested_by="configuration-api-bulk",
                timeout=5,
            )

            if response.get("message_type") == "NODE_ACK" and response.get("payload", {}).get("ack_type") == "applied":
                service.mark_config_pushed(node.id)
                success_count += 1
                results.append({
                    "node_id": node.id,
                    "status": "APPLIED",
                    "message": "Configuration applied successfully.",
                    "correlation_id": response.get("correlation_id"),
                })
                continue

            if response.get("message_type") == "NODE_ERROR":
                payload = response.get("payload", {})
                results.append({
                    "node_id": node.id,
                    "status": "ERROR",
                    "message": payload.get("message") or "Node rejected configuration apply.",
                    "code": payload.get("code"),
                    "retryable": bool(payload.get("retryable", False)),
                    "correlation_id": response.get("correlation_id"),
                })
                continue

            results.append({
                "node_id": node.id,
                "status": "ERROR",
                "message": f"Unexpected response type: {response.get('message_type')}",
                "correlation_id": response.get("correlation_id"),
            })
        except TimeoutError:
            results.append({
                "node_id": node.id,
                "status": "TIMEOUT",
                "message": "Node did not respond within 5 seconds. The node may be offline or busy.",
            })
        except Exception as exc:
            results.append({
                "node_id": node.id,
                "status": "ERROR",
                "message": str(exc),
            })

    _sync_runtime_topology(session)

    return {
        "status": "COMPLETED",
        "message": "Bulk configuration push completed.",
        "total_nodes": len(nodes),
        "pending_nodes": len(pending_nodes),
        "applied": success_count,
        "failed": len(pending_nodes) - success_count,
        "results": results,
    }