import json
import os
import signal
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
    topic_discovery_ack,
    topic_discovery_command,
    topic_discovery_hello,
    topic_ack,
    topic_command,
    topic_config,
    topic_error,
    topic_status,
)
from smart_irrigation_system.node.config.identity import NodeIdentity, DEFAULT_IDENTITY_PATH, save_node_identity
from smart_irrigation_system.node.config import config_loader
from smart_irrigation_system.node.core.controller.controller_core import ControllerCore
from smart_irrigation_system.node.core.enums import ControllerState
from smart_irrigation_system.node.utils.logger import get_logger


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
CONFIG_GLOBAL_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_global.json")
CONFIG_ZONES_PATH = os.path.join(BASE_DIR, "runtime/node/config/zones_config.json")
CONFIG_SECRETS_PATH = os.path.join(BASE_DIR, "runtime/node/config/config_secrets.json")


class MQTTClient(threading.Thread):
    def __init__(
        self,
        controller: ControllerCore,
        identity: NodeIdentity,
        broker_host: str | None = None,
        broker_port: int | None = None,
        snapshot_interval_seconds: int = 2,
        discovery_interval_seconds: int = 5,
        identity_path: str = DEFAULT_IDENTITY_PATH,
    ):
        super().__init__(daemon=True)
        self.controller = controller
        self.hardware_uid = identity.hardware_uid
        self.serial_number = identity.serial_number
        self.assigned_node_id = identity.assigned_node_id
        self.identity_path = identity_path
        self.broker_host = broker_host or os.getenv("MQTT_HOST", "localhost")
        self.broker_port = int(broker_port or os.getenv("MQTT_PORT", "1883"))
        self.snapshot_interval_seconds = snapshot_interval_seconds
        self.discovery_interval_seconds = discovery_interval_seconds

        self.client = mqtt.Client(client_id=f"sis_node_{self.hardware_uid}")
        self.logger = get_logger("MQTTClient")
        self._stop_event = threading.Event()
        self._state_lock = threading.RLock()

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.logger.info(
            "MQTTClient initialized for hardware_uid=%s, assigned_node_id=%s, broker=%s:%s",
            self.hardware_uid,
            self.assigned_node_id,
            broker_host,
            broker_port,
        )

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Connected to broker.")
            self._subscribe_active_topics()
        else:
            self.logger.error("MQTT connection failed with code %s", rc)

    def _on_message(self, client, userdata, msg):
        payload_raw = msg.payload.decode("utf-8")
        topic = msg.topic

        if topic.startswith("irrigation/"):
            self._handle_legacy_command(payload_raw)
            return

        if topic == topic_discovery_command(self.hardware_uid):
            self._handle_discovery_command(payload_raw)
            return

        try:
            envelope = decode_envelope(payload_raw)
            self._dispatch_envelope(envelope)
        except Exception as exc:
            self.logger.error("Error processing MQTT message on %s: %s", topic, exc)

    def _subscribe_active_topics(self) -> None:
        if self.assigned_node_id:
            self.client.subscribe(topic_command(self.assigned_node_id), qos=1)
            self.client.subscribe(topic_config(self.assigned_node_id), qos=1)
            self.client.subscribe(f"irrigation/{self.assigned_node_id}/command", qos=1)
            return

        self.client.subscribe(topic_discovery_command(self.hardware_uid), qos=1)

    def _handle_discovery_command(self, payload_raw: str) -> None:
        try:
            envelope = decode_envelope(payload_raw)
        except Exception as exc:
            self.logger.error("Failed to decode discovery message: %s", exc)
            return

        if envelope.get("message_type") == MessageType.CMD_ASSIGN_NODE_ID.value:
            self._handle_assign_node_id(envelope)
        else:
            self.logger.warning("Unhandled discovery message_type: %s", envelope.get("message_type"))

    def _handle_assign_node_id(self, envelope: dict[str, Any]) -> None:
        payload = envelope.get("payload", {})
        assigned_node_id = str(payload.get("assigned_node_id") or "").strip()
        if not assigned_node_id:
            self._error(
                envelope,
                code="INVALID_PAYLOAD",
                message="assigned_node_id is required for CMD_ASSIGN_NODE_ID",
                retryable=False,
            )
            return

        with self._state_lock:
            self.assigned_node_id = assigned_node_id
            save_node_identity(
                NodeIdentity(
                    hardware_uid=self.hardware_uid,
                    assigned_node_id=self.assigned_node_id,
                    serial_number=self.serial_number,
                    hostname=os.getenv("HOSTNAME") or None,
                ),
                self.identity_path,
            )

        self._subscribe_active_topics()
        self._publish_assignment_ack(envelope, assigned_node_id)
        self.logger.info("Node assigned persistent ID %s for hardware_uid=%s", assigned_node_id, self.hardware_uid)

    def _publish_assignment_ack(self, incoming: dict[str, Any], assigned_node_id: str) -> None:
        envelope = make_envelope(
            message_type=MessageType.NODE_ASSIGNMENT_ACK,
            node_id=self.hardware_uid,
            correlation_id=incoming.get("message_id"),
            payload={
                "assigned_node_id": assigned_node_id,
                "hardware_uid": self.hardware_uid,
                "status": "stored",
            },
        )
        self.client.publish(topic_discovery_ack(self.hardware_uid), json.dumps(envelope), qos=1)

    def publish_discovery_hello(self) -> None:
        envelope = make_envelope(
            message_type=MessageType.NODE_DISCOVERY_HELLO,
            node_id=self.hardware_uid,
            payload={
                "hardware_uid": self.hardware_uid,
                "serial_number": self.serial_number,
                "hostname": os.getenv("HOSTNAME") or None,
                "assigned_node_id": self.assigned_node_id,
            },
        )
        self.client.publish(topic_discovery_hello(), json.dumps(envelope), qos=1)

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
            self._handle_stop_irrigation(envelope)
            return

        if message_type == MessageType.CMD_STOP_CIRCUIT.value:
            self._handle_stop_circuit(envelope)
            return

        if message_type == MessageType.CMD_APPLY_CONFIG.value:
            self._handle_apply_config(envelope)
            return

        if message_type == MessageType.CMD_UNPAIR_NODE.value:
            self._handle_unpair_node(envelope)
            return

        self._error(envelope, code="UNKNOWN_COMMAND", message=f"Unsupported message_type: {message_type}", retryable=False)

    def _handle_unpair_node(self, envelope: dict[str, Any]) -> None:
        node_id = self._get_active_node_id()
        if not node_id:
            return

        expected_hardware_uid = str(envelope.get("payload", {}).get("hardware_uid") or "").strip()
        if expected_hardware_uid and expected_hardware_uid != self.hardware_uid:
            self._error(
                envelope,
                code="HARDWARE_UID_MISMATCH",
                message="CMD_UNPAIR_NODE hardware_uid does not match this node",
                retryable=False,
            )
            return

        ack = make_envelope(
            message_type=MessageType.NODE_UNPAIR_ACK,
            node_id=node_id,
            correlation_id=envelope.get("message_id"),
            payload={
                "hardware_uid": self.hardware_uid,
                "status": "unpaired",
            },
        )
        self.client.publish(topic_ack(node_id), json.dumps(ack), qos=1)

        with self._state_lock:
            previous_node_id = self.assigned_node_id
            self.assigned_node_id = None
            save_node_identity(
                NodeIdentity(
                    hardware_uid=self.hardware_uid,
                    assigned_node_id=None,
                    serial_number=self.serial_number,
                    hostname=os.getenv("HOSTNAME") or None,
                ),
                self.identity_path,
            )

        if previous_node_id:
            self.client.unsubscribe(topic_command(previous_node_id))
            self.client.unsubscribe(topic_config(previous_node_id))
            self.client.unsubscribe(f"irrigation/{previous_node_id}/command")

        self.client.subscribe(topic_discovery_command(self.hardware_uid), qos=1)
        self.publish_discovery_hello()
        self.logger.info("Node unpaired successfully. Switched back to discovery mode for hardware_uid=%s", self.hardware_uid)

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
        try:
            self.controller.start_manual_irrigation(zone_id, liter_amount)
            self._ack(envelope, AckType.COMPLETED)
        except Exception as exc:
            self.logger.error("Failed to start irrigation for zone %s: %s", zone_id, exc)
            self._error(
                envelope,
                code="IRRIGATION_START_FAILED",
                message=f"Failed to start irrigation for zone {zone_id}: {str(exc)}",
                retryable=True,
            )
            return
        
    def _handle_stop_irrigation(self, envelope: dict[str, Any]) -> None:
        self._ack(envelope, AckType.ACCEPTED)
        try:
            self.controller.stop_all_irrigation()
            self._ack(envelope, AckType.COMPLETED)
        except Exception as exc:
            self.logger.error("Failed to stop irrigation: %s", exc)
            self._error(
                envelope,
                code="IRRIGATION_STOP_FAILED",
                message=f"Failed to stop irrigation: {str(exc)}",
                retryable=True,
            )

    def _handle_stop_circuit(self, envelope: dict[str, Any]) -> None:
        payload = envelope["payload"]
        try:
            circuit_id = int(payload["circuit_id"])
        except (KeyError, ValueError, TypeError):
            self._error(
                envelope,
                code="INVALID_PAYLOAD",
                message="circuit_id is required for CMD_STOP_CIRCUIT",
                retryable=False,
            )
            return

        self._ack(envelope, AckType.ACCEPTED)
        try:
            self.controller.stop_circuit_irrigation(circuit_id)
            self._ack(envelope, AckType.COMPLETED)
        except Exception as exc:
            self.logger.error("Failed to stop circuit %s: %s", circuit_id, exc)
            self._error(
                envelope,
                code="CIRCUIT_STOP_FAILED",
                message=f"Failed to stop circuit {circuit_id}: {str(exc)}",
                retryable=True,
            )

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

        # Strict preflight validation of config before acknowledging acceptance
        try:
            config_loader.validate_legacy_runtime_config(legacy_runtime_config, CONFIG_SECRETS_PATH)
        except ValueError as exc:
            self._error(
                envelope,
                code="CONFIG_INVALID",
                message=str(exc),
                retryable=False,
            )
            return

        # Check if irrigation is currently running; cannot apply config during active irrigation
        if self.controller.controller_state != ControllerState.IDLE:
            self._error(
                envelope,
                code="CONFIG_APPLY_BLOCKED",
                message=f"Cannot apply config while controller is {self.controller.controller_state.value}. "
                        f"Wait for ongoing irrigation tasks to complete.",
                retryable=True,
            )
            return

        self._ack(envelope, AckType.ACCEPTED)
        self.logger.info("Config apply accepted. Mode: %s. Validating and applying config...", apply_mode)

        try:
            if apply_mode == ApplyMode.VALIDATE_ONLY.value:
                json.dumps(config_global)
                json.dumps(zones_config)
                self._ack(envelope, AckType.APPLIED)
            else:
                self._write_json(CONFIG_GLOBAL_PATH, config_global)
                self._write_json(CONFIG_ZONES_PATH, zones_config)
                self.logger.info("Config apply completed. Written config to disk. Mode: %s", apply_mode)
                self._ack(envelope, AckType.APPLIED)
                
                # Give MQTT a moment to publish the ACK, then gracefully shutdown and restart
                self.logger.info("Config applied and ACK sent. Gracefully shutting down node process for restart...")
                time.sleep(0.5)  # Allow MQTT message to be sent
                self.controller.shutdown(force=False)
                self._terminate_process_for_restart()
                
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

    def _terminate_process_for_restart(self) -> None:
        """Terminate the entire node process so container restart policy can relaunch it."""
        pid = os.getpid()
        self.logger.info("Sending SIGTERM to process pid=%s for node restart.", pid)
        os.kill(pid, signal.SIGTERM)

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
        node_id = self._get_active_node_id()
        if not node_id:
            self.logger.debug("Skipping status snapshot until node is assigned an ID.")
            return

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
            node_id=node_id,
            payload={
                "controller_state": str(status.get("controller_state", "IDLE")).lower(),
                "auto_enabled": bool(status.get("auto_enabled", True)),
                "auto_paused": bool(status.get("auto_paused", False)),
                "zones": zones_payload,
                "current_tasks": tasks_payload,
                "alerts": [] if include_alerts else [],
            },
        )
        self.client.publish(topic_status(node_id), json.dumps(envelope), qos=1)

    def _ack(self, incoming: dict[str, Any], ack_type: AckType) -> None:
        node_id = self._get_active_node_id()
        if not node_id:
            self.logger.debug("Skipping ACK until node is assigned an ID.")
            return

        envelope = make_envelope(
            message_type=MessageType.NODE_ACK,
            node_id=node_id,
            correlation_id=incoming["message_id"],
            payload={
                "ack_type": ack_type.value,
                "for_message_type": incoming["message_type"],
                "details": {},
            },
        )
        self.client.publish(topic_ack(node_id), json.dumps(envelope), qos=1)

    def _error(self, incoming: dict[str, Any], code: str, message: str, retryable: bool) -> None:
        node_id = self._get_active_node_id()
        if not node_id:
            self.logger.debug("Skipping ERROR until node is assigned an ID.")
            return

        envelope = make_envelope(
            message_type=MessageType.NODE_ERROR,
            node_id=node_id,
            correlation_id=incoming.get("message_id"),
            payload={
                "code": code,
                "message": message,
                "retryable": retryable,
                "details": {},
            },
        )
        self.client.publish(topic_error(node_id), json.dumps(envelope), qos=1)

    def _get_active_node_id(self) -> str | None:
        with self._state_lock:
            return self.assigned_node_id

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
        last_discovery = 0.0
        try:
            while not self._stop_event.is_set():
                now = time.monotonic()
                if self.assigned_node_id:
                    if now - last_snapshot >= self.snapshot_interval_seconds:
                        self.publish_status_snapshot(include_alerts=True, include_tasks=True)
                        last_snapshot = now
                else:
                    if now - last_discovery >= self.discovery_interval_seconds:
                        self.publish_discovery_hello()
                        last_discovery = now

                time.sleep(0.2)
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("MQTT client stopped.")

    def stop(self):
        self._stop_event.set()
