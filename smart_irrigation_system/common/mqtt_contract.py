from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
import json
from typing import Any
from uuid import uuid4


MQTT_CONTRACT_VERSION = 1


class MessageType(StrEnum):
    NODE_STATUS_SNAPSHOT = "NODE_STATUS_SNAPSHOT"
    NODE_HEARTBEAT = "NODE_HEARTBEAT"
    NODE_ACK = "NODE_ACK"
    NODE_ERROR = "NODE_ERROR"
    CMD_GET_STATUS = "CMD_GET_STATUS"
    CMD_START_IRRIGATION = "CMD_START_IRRIGATION"
    CMD_STOP_IRRIGATION = "CMD_STOP_IRRIGATION"
    CMD_APPLY_CONFIG = "CMD_APPLY_CONFIG"


class AckType(StrEnum):
    ACCEPTED = "accepted"
    APPLIED = "applied"
    COMPLETED = "completed"


class ApplyMode(StrEnum):
    VALIDATE_ONLY = "validate_only"
    APPLY_NOW = "apply_now"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_node_id_from_topic(topic: str) -> str | None:
    # Expected: sis/v1/nodes/{node_id}/{suffix}
    parts = topic.split("/")
    if len(parts) < 5:
        return None
    if parts[0] != "sis" or parts[1] != "v1" or parts[2] != "nodes":
        return None
    return parts[3]


def topic_status(node_id: str) -> str:
    return f"sis/v1/nodes/{node_id}/status"


def topic_event(node_id: str) -> str:
    return f"sis/v1/nodes/{node_id}/event"


def topic_ack(node_id: str) -> str:
    return f"sis/v1/nodes/{node_id}/ack"


def topic_error(node_id: str) -> str:
    return f"sis/v1/nodes/{node_id}/error"


def topic_command(node_id: str) -> str:
    return f"sis/v1/nodes/{node_id}/command"


def topic_config(node_id: str) -> str:
    return f"sis/v1/nodes/{node_id}/config"


def make_envelope(
    *,
    message_type: MessageType,
    node_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    return {
        "version": MQTT_CONTRACT_VERSION,
        "message_id": str(uuid4()),
        "message_type": message_type.value,
        "node_id": node_id,
        "sent_at": utc_now_iso(),
        "correlation_id": correlation_id,
        "payload": payload,
    }


def decode_envelope(raw_payload: str) -> dict[str, Any]:
    data = json.loads(raw_payload)
    validate_envelope(data)
    return data


def validate_envelope(data: dict[str, Any]) -> None:
    required = [
        "version",
        "message_id",
        "message_type",
        "node_id",
        "sent_at",
        "correlation_id",
        "payload",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Missing envelope fields: {missing}")

    if data["version"] != MQTT_CONTRACT_VERSION:
        raise ValueError(f"Unsupported MQTT contract version: {data['version']}")

    if not isinstance(data["payload"], dict):
        raise ValueError("Envelope payload must be an object")

    message_type = data.get("message_type")
    if message_type not in {m.value for m in MessageType}:
        raise ValueError(f"Unknown message_type: {message_type}")
