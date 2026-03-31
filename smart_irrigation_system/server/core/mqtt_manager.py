import json
import os
import threading
from typing import Any

import paho.mqtt.client as mqtt

from smart_irrigation_system.common.mqtt_contract import (
    AckType,
    ApplyMode,
    MessageType,
    decode_envelope,
    parse_iso_datetime,
    topic_ack,
    topic_command,
    topic_config,
    topic_error,
    make_envelope,
)
from smart_irrigation_system.server.runtime.schemas.live import AlertType, ZoneStatus
from smart_irrigation_system.server.runtime.services.live_service import get_live_store
from smart_irrigation_system.server.utils.logger import get_logger


class MQTTManager(threading.Thread):
    def __init__(self, node_registry=None, broker_host: str | None = None, broker_port: int | None = None):
        super().__init__(daemon=True)
        self.logger = get_logger("MQTTManager")
        self.node_registry = node_registry
        self.broker_host = broker_host or os.getenv("MQTT_HOST", "localhost")
        self.broker_port = int(broker_port or os.getenv("MQTT_PORT", "1883"))
        self.client = mqtt.Client(client_id="sis_server_mqtt_manager")
        self._stop_event = threading.Event()
        self._seen_alert_keys: set[tuple[str, str, str, str]] = set()
        self.live_store = get_live_store()

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Connected to MQTT broker.")
            client.subscribe("sis/v1/nodes/+/status", qos=1)
            client.subscribe("sis/v1/nodes/+/event", qos=1)
            client.subscribe("sis/v1/nodes/+/ack", qos=1)
            client.subscribe("sis/v1/nodes/+/error", qos=1)
            # Temporary legacy subscription for transition period.
            client.subscribe("irrigation/+/status", qos=1)
        else:
            self.logger.error("MQTT connection failed with code %s", rc)

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_raw = msg.payload.decode("utf-8")

        if topic.startswith("irrigation/"):
            self._handle_legacy_status(topic=topic, payload_raw=payload_raw)
            return

        try:
            envelope = decode_envelope(payload_raw)
        except Exception as exc:
            self.logger.error("Failed to decode MQTT envelope on %s: %s", topic, exc)
            return

        msg_type = envelope["message_type"]
        if msg_type == MessageType.NODE_HEARTBEAT.value:
            self._handle_node_heartbeat(envelope)
        elif msg_type == MessageType.NODE_STATUS_SNAPSHOT.value:
            self._handle_node_status_snapshot(envelope)
        elif msg_type == MessageType.NODE_ACK.value:
            self.logger.debug("Node ACK received: %s", envelope)
        elif msg_type == MessageType.NODE_ERROR.value:
            self.logger.warning("Node ERROR received: %s", envelope)
        else:
            self.logger.warning("Unhandled message_type %s on topic %s", msg_type, topic)

    def _handle_node_heartbeat(self, envelope: dict[str, Any]) -> None:
        node_id_str = str(envelope["node_id"])
        node_id_int = self._to_node_id_int(node_id_str)
        seen_at = parse_iso_datetime(envelope["payload"].get("updated_at")) or parse_iso_datetime(envelope.get("sent_at"))

        if node_id_int is not None:
            self.live_store.upsert_node_heartbeat(node_id=node_id_int, seen_at=seen_at)

        self._update_legacy_registry(node_id=node_id_str, controller_state=envelope["payload"].get("controller_state", "IDLE"), zones=[])

    def _handle_node_status_snapshot(self, envelope: dict[str, Any]) -> None:
        payload = envelope["payload"]
        node_id_str = str(envelope["node_id"])
        node_id_int = self._to_node_id_int(node_id_str)
        if node_id_int is None:
            self.logger.warning("Unable to map node_id '%s' to integer id for runtime store", node_id_str)
            return

        sent_at = parse_iso_datetime(envelope.get("sent_at"))
        self.live_store.upsert_node_heartbeat(node_id=node_id_int, seen_at=sent_at)

        zones = payload.get("zones", [])
        for zone in zones:
            zone_id = zone.get("zone_id")
            if zone_id is None:
                continue

            zone_status = self._to_zone_status(zone.get("status", "offline"))
            zone_updated_at = parse_iso_datetime(zone.get("updated_at")) or sent_at
            self.live_store.upsert_zone_state(
                node_id=node_id_int,
                zone_id=int(zone_id),
                status=zone_status,
                progress_percent=zone.get("progress_percent"),
                last_run=parse_iso_datetime(zone.get("last_run")),
                zone_name=zone.get("zone_name"),
                enabled=zone.get("enabled"),
                seen_at=zone_updated_at,
            )

        self._replace_current_tasks(node_id=node_id_int, payload=payload, sent_at=sent_at)
        self._append_new_alerts(payload)

        self._update_legacy_registry(
            node_id=node_id_str,
            controller_state=payload.get("controller_state", "IDLE"),
            zones=[int(z.get("zone_id")) for z in zones if z.get("status") == "irrigating" and z.get("zone_id") is not None],
        )

    def _replace_current_tasks(self, node_id: int, payload: dict[str, Any], sent_at) -> None:
        # MVP approach: update/insert all reported tasks. Removal of stale task IDs can be event-driven later.
        for task in payload.get("current_tasks", []):
            task_id = task.get("task_id")
            if task_id is None:
                continue

            self.live_store.upsert_current_task(
                task_id=int(task_id),
                zone_name=task.get("zone_name", f"Zone {task.get('zone_id', '?')}"),
                progress_percent=float(task.get("progress_percent", 0.0)),
                current_volume=float(task.get("current_volume", 0.0)),
                target_volume=float(task.get("target_volume", 0.0)),
                remaining_minutes=int(task.get("remaining_minutes", 0)),
                zone_id=task.get("zone_id"),
                seen_at=parse_iso_datetime(task.get("updated_at")) or sent_at,
            )

    def _append_new_alerts(self, payload: dict[str, Any]) -> None:
        for alert in payload.get("alerts", []):
            level = str(alert.get("level", "warning")).lower()
            title = str(alert.get("title", "Alert"))
            message = str(alert.get("message", ""))
            timestamp_raw = str(alert.get("timestamp") or "")
            dedup_key = (level, title, message, timestamp_raw)
            if dedup_key in self._seen_alert_keys:
                continue

            self._seen_alert_keys.add(dedup_key)
            alert_type = AlertType.ERROR if level == "error" else AlertType.WARNING
            self.live_store.add_alert(
                alert_type=alert_type,
                title=title,
                message=message,
                timestamp=parse_iso_datetime(timestamp_raw),
            )

    def _handle_legacy_status(self, topic: str, payload_raw: str) -> None:
        # Legacy topic format: irrigation/{node_id}/status
        parts = topic.split("/")
        if len(parts) < 3:
            return
        node_id = parts[1]
        self.logger.debug("Legacy MQTT status received from %s: %s", node_id, payload_raw)
        if self.node_registry:
            self.node_registry.update_node_status(node_id, payload_raw)

    def _to_zone_status(self, value: str) -> ZoneStatus:
        normalized = str(value).lower()
        mapping = {
            "idle": ZoneStatus.IDLE,
            "irrigating": ZoneStatus.IRRIGATING,
            "waiting": ZoneStatus.IDLE,
            "error": ZoneStatus.ERROR,
            "stopping": ZoneStatus.STOPPING,
            "offline": ZoneStatus.OFFLINE,
        }
        return mapping.get(normalized, ZoneStatus.OFFLINE)

    def _to_node_id_int(self, node_id: str) -> int | None:
        if node_id.isdigit():
            return int(node_id)
        if node_id.startswith("node") and node_id[4:].isdigit():
            return int(node_id[4:])
        return None

    def _update_legacy_registry(self, node_id: str, controller_state: str, zones: list[int]) -> None:
        if not self.node_registry:
            return
        status = (
            f"Controller State: {str(controller_state).upper()}, "
            "Auto Enabled: True, "
            "Auto Paused: False, "
            f"Currently Irrigating Zones: {zones}"
        )
        self.node_registry.update_node_status(node_id, status)

    # ------------------- Public methods ------------------- #

    def publish_get_status(self, node_id: str, include_alerts: bool = True, include_tasks: bool = True) -> str:
        envelope = make_envelope(
            message_type=MessageType.CMD_GET_STATUS,
            node_id=node_id,
            payload={
                "include_alerts": include_alerts,
                "include_tasks": include_tasks,
            },
        )
        self.client.publish(topic_command(node_id), json.dumps(envelope), qos=1)
        return str(envelope["message_id"])

    def publish_start_irrigation(self, node_id: str, zone_id: int, liter_amount: float) -> str:
        envelope = make_envelope(
            message_type=MessageType.CMD_START_IRRIGATION,
            node_id=node_id,
            payload={
                "zone_id": int(zone_id),
                "liter_amount": float(liter_amount),
            },
        )
        self.client.publish(topic_command(node_id), json.dumps(envelope), qos=1)
        return str(envelope["message_id"])

    def publish_stop_irrigation(self, node_id: str) -> str:
        envelope = make_envelope(
            message_type=MessageType.CMD_STOP_IRRIGATION,
            node_id=node_id,
            payload={},
        )
        self.client.publish(topic_command(node_id), json.dumps(envelope), qos=1)
        return str(envelope["message_id"])

    def publish_apply_config(
        self,
        node_id: str,
        config_revision: str,
        legacy_runtime_config: dict[str, Any],
        apply_mode: ApplyMode = ApplyMode.APPLY_NOW,
        requested_by: str | None = None,
    ) -> str:
        envelope = make_envelope(
            message_type=MessageType.CMD_APPLY_CONFIG,
            node_id=node_id,
            payload={
                "config_revision": config_revision,
                "apply_mode": apply_mode.value,
                "legacy_runtime_config": legacy_runtime_config,
                "requested_by": requested_by,
            },
        )
        self.client.publish(topic_config(node_id), json.dumps(envelope), qos=1)
        return str(envelope["message_id"])

    def publish_command(self, node_id: str, command: dict):
        """Legacy adapter used by existing API routes and server_core."""
        action = command.get("action")
        if action == "get_status":
            self.publish_get_status(node_id)
            return
        if action == "start_irrigation":
            self.publish_start_irrigation(
                node_id=node_id,
                zone_id=int(command.get("zone_id")),
                liter_amount=float(command.get("liter_amount")),
            )
            return
        if action == "stop_irrigation":
            self.publish_stop_irrigation(node_id=node_id)
            return

        self.logger.warning("Unknown legacy command action: %s", action)

    def run(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        except Exception as exc:
            self.logger.error("Failed to connect to MQTT broker: %s", exc)
            return

        self.client.loop_start()
        self.logger.info("MQTT loop started.")
        while not self._stop_event.is_set():
            self._stop_event.wait(1)
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("MQTT client stopped.")

    def stop(self):
        self._stop_event.set()
