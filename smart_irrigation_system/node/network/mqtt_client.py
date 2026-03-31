import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt

from smart_irrigation_system.common.mqtt_contract import (
    AckType,
    ApplyMode,
    MessageType,
    decode_envelope,
    make_envelope,
    topic_ack,
    topic_command,
    topic_config,
    topic_error,
    topic_status,
)
from smart_irrigation_system.node.core.controller.controller_core import ControllerCore
from smart_irrigation_system.node.utils.logger import get_logger


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)
CONFIG_GLOBAL_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_global.json")
CONFIG_ZONES_PATH = os.path.join(BASE_DIR, "runtime/node/config/zones_config.json")


class MQTTClient(threading.Thread):
    def __init__(
        self,
        controller: ControllerCore,
        node_id: str = "node1",
        broker_host: str | None = None,
        broker_port: int | None = None,
        snapshot_interval_seconds: int = 5,
    ):
        super().__init__(daemon=True)
        self.controller = controller
        self.node_id = node_id
        self.broker_host = broker_host or os.getenv("MQTT_HOST", "localhost")
        self.broker_port = int(broker_port or os.getenv("MQTT_PORT", "1883"))
        self.snapshot_interval_seconds = snapshot_interval_seconds

        self.client = mqtt.Client(client_id=f"sis_node_{node_id}")
        self.logger = get_logger("MQTTClient")
        self._stop_event = threading.Event()

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.logger.info("MQTTClient initialized for node_id=%s, broker=%s:%s", node_id, broker_host, broker_port)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Connected to broker.")
            client.subscribe(topic_command(self.node_id), qos=1)
            client.subscribe(topic_config(self.node_id), qos=1)
            # Legacy compatibility topic for transition period.
            client.subscribe(f"irrigation/{self.node_id}/command", qos=1)
        else:
            self.logger.error("MQTT connection failed with code %s", rc)

    def _on_message(self, client, userdata, msg):
        payload_raw = msg.payload.decode("utf-8")
        topic = msg.topic

        if topic.startswith("irrigation/"):
            self._handle_legacy_command(payload_raw)
            return

        try:
            envelope = decode_envelope(payload_raw)
            self._dispatch_envelope(envelope)
        except Exception as exc:
            self.logger.error("Error processing MQTT message on %s: %s", topic, exc)

    def _dispatch_envelope(self, envelope: dict[str, Any]) -> None:
        message_type = envelope["message_type"]

        if message_type == MessageType.CMD_GET_STATUS.value:
            self.publish_status_snapshot(
                include_alerts=bool(envelope["payload"].get("include_alerts", True)),
                include_tasks=bool(envelope["payload"].get("include_tasks", True)),
            )
            return

        if message_type == MessageType.CMD_START_IRRIGATION.value:
            self._handle_start_irrigation(envelope)
            return

        if message_type == MessageType.CMD_STOP_IRRIGATION.value:
            self._ack(envelope, AckType.ACCEPTED)
            self.controller.stop_all_irrigation()
            self._ack(envelope, AckType.COMPLETED)
            return

        if message_type == MessageType.CMD_APPLY_CONFIG.value:
            self._handle_apply_config(envelope)
            return

        self._error(envelope, code="UNKNOWN_COMMAND", message=f"Unsupported message_type: {message_type}", retryable=False)

    def _handle_start_irrigation(self, envelope: dict[str, Any]) -> None:
        payload = envelope["payload"]
        try:
            zone_id = int(payload["zone_id"])
            liter_amount = float(payload["liter_amount"])
        except Exception:
            self._error(
                envelope,
                code="INVALID_PAYLOAD",
                message="zone_id and liter_amount are required for CMD_START_IRRIGATION",
                retryable=False,
            )
            return

        self._ack(envelope, AckType.ACCEPTED)
        self.controller.start_manual_irrigation(zone_id, liter_amount)
        self._ack(envelope, AckType.COMPLETED)

    def _handle_apply_config(self, envelope: dict[str, Any]) -> None:
        payload = envelope["payload"]
        apply_mode = str(payload.get("apply_mode", ApplyMode.APPLY_NOW.value))
        legacy_runtime_config = payload.get("legacy_runtime_config")

        if not isinstance(legacy_runtime_config, dict):
            self._error(
                envelope,
                code="INVALID_PAYLOAD",
                message="legacy_runtime_config must be an object",
                retryable=False,
            )
            return

        config_global = legacy_runtime_config.get("config_global")
        zones_config = legacy_runtime_config.get("zones_config")

        if not isinstance(config_global, dict) or not isinstance(zones_config, dict):
            self._error(
                envelope,
                code="INVALID_PAYLOAD",
                message="legacy_runtime_config must contain config_global and zones_config objects",
                retryable=False,
            )
            return

        self._ack(envelope, AckType.ACCEPTED)

        try:
            if apply_mode == ApplyMode.VALIDATE_ONLY.value:
                json.dumps(config_global)
                json.dumps(zones_config)
            else:
                self._write_json(CONFIG_GLOBAL_PATH, config_global)
                self._write_json(CONFIG_ZONES_PATH, zones_config)
                # Runtime in-place reload is not implemented in ControllerCore yet.
            self._ack(envelope, AckType.APPLIED)
        except Exception as exc:
            self._error(
                envelope,
                code="CONFIG_APPLY_FAILED",
                message=str(exc),
                retryable=True,
            )

    def _write_json(self, path: str, data: dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def _handle_legacy_command(self, payload_raw: str) -> None:
        try:
            command = json.loads(payload_raw)
        except json.JSONDecodeError:
            self.logger.error("Failed to decode legacy command JSON")
            return

        action = command.get("action")
        if action == "get_status":
            self.publish_status_snapshot(include_alerts=True, include_tasks=True)
        elif action == "start_irrigation":
            try:
                self.controller.start_manual_irrigation(int(command.get("zone_id")), float(command.get("liter_amount")))
            except Exception as exc:
                self.logger.error("Legacy start_irrigation failed: %s", exc)
        elif action == "stop_irrigation":
            self.controller.stop_all_irrigation()
        else:
            self.logger.warning("Unknown legacy command action: %s", action)

    def publish_status_snapshot(self, include_alerts: bool = True, include_tasks: bool = True) -> None:
        status = self.controller.get_status()
        zones_payload: list[dict[str, Any]] = []
        tasks_payload: list[dict[str, Any]] = []

        now_iso = self._now_iso()
        for circuit in self.controller.circuits.values():
            runtime = circuit.runtime_status
            zone_status = self._map_zone_state(runtime.state.value)

            zones_payload.append(
                {
                    "zone_id": circuit.id,
                    "zone_name": circuit.name,
                    "status": zone_status,
                    "enabled": circuit.enabled,
                    "progress_percent": runtime.progress_percentage,
                    "last_run": None,
                    "updated_at": now_iso,
                }
            )

            if include_tasks and runtime.is_irrigating:
                remaining_minutes = None
                if runtime.target_duration is not None and runtime.current_duration is not None:
                    remaining_seconds = max(runtime.target_duration - runtime.current_duration, 0)
                    remaining_minutes = int(round(remaining_seconds / 60.0))

                tasks_payload.append(
                    {
                        "task_id": int(circuit.id),
                        "zone_id": int(circuit.id),
                        "zone_name": circuit.name,
                        "progress_percent": float(runtime.progress_percentage or 0.0),
                        "current_volume": float(runtime.current_volume or 0.0),
                        "target_volume": float(runtime.target_volume or 0.0),
                        "remaining_minutes": int(remaining_minutes or 0),
                        "updated_at": now_iso,
                    }
                )

        envelope = make_envelope(
            message_type=MessageType.NODE_STATUS_SNAPSHOT,
            node_id=self.node_id,
            payload={
                "controller_state": str(status.get("controller_state", "IDLE")).lower(),
                "auto_enabled": bool(status.get("auto_enabled", True)),
                "auto_paused": bool(status.get("auto_paused", False)),
                "zones": zones_payload,
                "current_tasks": tasks_payload,
                "alerts": [] if include_alerts else [],
            },
        )
        self.client.publish(topic_status(self.node_id), json.dumps(envelope), qos=1)

    def _ack(self, incoming: dict[str, Any], ack_type: AckType) -> None:
        envelope = make_envelope(
            message_type=MessageType.NODE_ACK,
            node_id=self.node_id,
            correlation_id=incoming["message_id"],
            payload={
                "ack_type": ack_type.value,
                "for_message_type": incoming["message_type"],
                "details": {},
            },
        )
        self.client.publish(topic_ack(self.node_id), json.dumps(envelope), qos=1)

    def _error(self, incoming: dict[str, Any], code: str, message: str, retryable: bool) -> None:
        envelope = make_envelope(
            message_type=MessageType.NODE_ERROR,
            node_id=self.node_id,
            correlation_id=incoming.get("message_id"),
            payload={
                "code": code,
                "message": message,
                "retryable": retryable,
                "details": {},
            },
        )
        self.client.publish(topic_error(self.node_id), json.dumps(envelope), qos=1)

    def _map_zone_state(self, state_value: str) -> str:
        normalized = str(state_value).lower()
        mapping = {
            "idle": "idle",
            "irrigating": "irrigating",
            "waiting": "waiting",
            "error": "error",
            "disabled": "idle",
        }
        return mapping.get(normalized, "offline")

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def run(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        except Exception as exc:
            self.logger.error("Failed to connect to MQTT broker: %s", exc)
            return

        self.client.loop_start()
        self.logger.info("MQTT loop started.")

        last_snapshot = 0.0
        try:
            while not self._stop_event.is_set():
                now = time.monotonic()
                if now - last_snapshot >= self.snapshot_interval_seconds:
                    self.publish_status_snapshot(include_alerts=True, include_tasks=True)
                    last_snapshot = now

                time.sleep(0.2)
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("MQTT client stopped.")

    def stop(self):
        self._stop_event.set()
