from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from smart_irrigation_system.common.mqtt_contract import AckType, MessageType
from smart_irrigation_system.server.core.server_core import IrrigationServer


router = APIRouter()
server = IrrigationServer()


class StartIrrigationRequest(BaseModel):
	zone_id: int = Field(..., description="ID of the irrigation zone to start")
	liter_amount: float = Field(..., description="Target water volume in liters")


class StopZoneRequest(BaseModel):
	zone_id: int = Field(..., description="ID of the irrigation zone to stop")


def _raise_for_node_error(response: dict[str, Any]) -> None:
	payload = response.get("payload", {})
	retryable = bool(payload.get("retryable", False))
	status_code = 409 if retryable else 400
	raise HTTPException(
		status_code=status_code,
		detail={
			"message_type": response.get("message_type"),
			"code": payload.get("code"),
			"message": payload.get("message"),
			"retryable": retryable,
			"correlation_id": response.get("correlation_id"),
		},
	)


def _handle_terminal_response(response: dict[str, Any]) -> dict[str, Any]:
	message_type = response.get("message_type")
	if message_type == MessageType.NODE_ERROR.value:
		_raise_for_node_error(response)

	if message_type != MessageType.NODE_ACK.value:
		raise HTTPException(
			status_code=502,
			detail={
				"message": "Unexpected response type from node",
				"response": response,
			},
		)

	ack_type = response.get("payload", {}).get("ack_type")
	if ack_type != AckType.COMPLETED.value:
		raise HTTPException(
			status_code=502,
			detail={
				"message": "Unexpected ACK type from node",
				"ack_type": ack_type,
				"response": response,
			},
		)

	return response


def _handle_mqtt_timeout(operation: str, timeout_seconds: int, node_id: str | None = None) -> HTTPException:
	detail: dict[str, Any] = {
		"message": f"Node did not finish {operation} within {timeout_seconds}s",
		"retryable": True,
	}
	if node_id is not None:
		detail["node_id"] = node_id
	return HTTPException(status_code=504, detail=detail)


def _handle_mqtt_failure(operation: str, exc: Exception, node_id: str | None = None) -> HTTPException:
	detail: dict[str, Any] = {
		"message": f"Failed to {operation}",
		"error": str(exc),
		"retryable": True,
	}
	if node_id is not None:
		detail["node_id"] = node_id
	return HTTPException(status_code=503, detail=detail)


@router.post(
	"/start-irrigation",
	summary="Start manual irrigation on a zone",
)
def start_irrigation(
	req: StartIrrigationRequest = Body(...),
	wait_for_response: bool = Query(True, description="Wait for node ACK/ERROR before returning"),
	timeout_seconds: int = Query(5, ge=1, le=60, description="Timeout for synchronous mode"),
) -> dict[str, Any]:
	node_id = server.node_topology_service.get_node_for_zone(req.zone_id)
	if node_id is None:
		raise HTTPException(status_code=404, detail={"message": f"No node is assigned to zone {req.zone_id}"})

	if wait_for_response:
		try:
			response = server.mqtt_manager.publish_start_irrigation_and_wait(
				node_id=node_id,
				zone_id=req.zone_id,
				liter_amount=req.liter_amount,
				timeout=timeout_seconds,
			)
		except TimeoutError:
			raise _handle_mqtt_timeout("start irrigation", timeout_seconds, node_id=node_id)
		except Exception as exc:
			raise _handle_mqtt_failure("start irrigation", exc, node_id=node_id)
		return {
			"status": "COMPLETED",
			"mode": "sync",
			"node_id": node_id,
			"zone_id": req.zone_id,
			"response": _handle_terminal_response(response),
		}

	try:
		message_id = server.mqtt_manager.publish_start_irrigation(
			node_id=node_id,
			zone_id=req.zone_id,
			liter_amount=req.liter_amount,
		)
	except Exception as exc:
		raise _handle_mqtt_failure("start irrigation", exc, node_id=node_id)
	return {
		"status": "SENT",
		"mode": "async",
		"node_id": node_id,
		"zone_id": req.zone_id,
		"message_id": message_id,
	}


@router.post(
	"/stop-zone",
	summary="Stop irrigation for a specific zone",
)
def stop_zone(
	req: StopZoneRequest = Body(...),
	wait_for_response: bool = Query(True, description="Wait for node ACK/ERROR before returning"),
	timeout_seconds: int = Query(5, ge=1, le=60, description="Timeout for synchronous mode"),
) -> dict[str, Any]:
	node_id = server.node_topology_service.get_node_for_zone(req.zone_id)
	if node_id is None:
		raise HTTPException(status_code=404, detail={"message": f"No node is assigned to zone {req.zone_id}"})

	if wait_for_response:
		try:
			response = server.mqtt_manager.publish_stop_circuit_and_wait(
				node_id=node_id,
				circuit_id=req.zone_id,
				timeout=timeout_seconds,
			)
		except TimeoutError:
			raise _handle_mqtt_timeout("stop zone", timeout_seconds, node_id=node_id)
		except Exception as exc:
			raise _handle_mqtt_failure("stop zone", exc, node_id=node_id)
		return {
			"status": "COMPLETED",
			"mode": "sync",
			"node_id": node_id,
			"zone_id": req.zone_id,
			"response": _handle_terminal_response(response),
		}

	try:
		message_id = server.mqtt_manager.publish_stop_circuit(
			node_id=node_id,
			circuit_id=req.zone_id,
		)
	except Exception as exc:
		raise _handle_mqtt_failure("stop zone", exc, node_id=node_id)
	return {
		"status": "SENT",
		"mode": "async",
		"node_id": node_id,
		"zone_id": req.zone_id,
		"message_id": message_id,
	}


@router.post(
	"/stop-irrigation",
	summary="Stop irrigation on all nodes",
)
def stop_irrigation(
	wait_for_response: bool = Query(True, description="Wait for node ACK/ERROR before returning"),
	timeout_seconds: int = Query(5, ge=1, le=60, description="Timeout for synchronous mode"),
) -> dict[str, Any]:
	node_ids = list(server.node_topology_service.get_all_node_ids())

	if wait_for_response:
		results: list[dict[str, Any]] = []
		for node_id in node_ids:
			try:
				response = server.mqtt_manager.publish_stop_irrigation_and_wait(
					node_id=node_id,
					timeout=timeout_seconds,
				)
			except TimeoutError:
				raise _handle_mqtt_timeout("stop irrigation", timeout_seconds, node_id=node_id)
			except Exception as exc:
				raise _handle_mqtt_failure("stop irrigation", exc, node_id=node_id)
			results.append(
				{
					"node_id": node_id,
					"response": _handle_terminal_response(response),
				}
			)

		return {
			"status": "COMPLETED",
			"mode": "sync",
			"nodes": results,
		}

	message_ids = [
		{
			"node_id": node_id,
			"message_id": server.mqtt_manager.publish_stop_irrigation(node_id=node_id),
		}
		for node_id in node_ids
	]
	return {
		"status": "SENT",
		"mode": "async",
		"nodes": message_ids,
	}
