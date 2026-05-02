from __future__ import annotations

from dataclasses import dataclass, field

from smart_irrigation_system.common.mqtt_contract import (
    MessageType,
    decode_envelope,
    make_envelope,
    topic_command,
    topic_discovery_command,
    topic_discovery_hello,
)
from smart_irrigation_system.node.config.identity import NodeIdentity, load_node_identity, save_node_identity
from smart_irrigation_system.node.network.mqtt_client import MQTTClient
from smart_irrigation_system.server.core.mqtt_manager import MQTTManager
from smart_irrigation_system.server.runtime.api.discovery import list_discovered_devices
from smart_irrigation_system.server.runtime.schemas.discovery import DiscoveredDeviceRead
from smart_irrigation_system.server.runtime.schemas.live import ZoneStatus
from smart_irrigation_system.server.runtime.state.live_store import RuntimeLiveStore


@dataclass
class FakePublishResult:
    rc: int = 0


@dataclass
class FakeMQTTClient:
    published: list[tuple[str, str, int]] = field(default_factory=list)
    subscriptions: list[tuple[str, int]] = field(default_factory=list)
    unsubscriptions: list[tuple[str, int]] = field(default_factory=list)
    on_connect: object | None = None
    on_message: object | None = None

    def subscribe(self, topic: str, qos: int = 0):
        self.subscriptions.append((topic, qos))

    def publish(self, topic: str, payload: str, qos: int = 0):
        self.published.append((topic, payload, qos))
        return FakePublishResult()

    def unsubscribe(self, topic: str, qos: int = 0):
        self.unsubscriptions.append((topic, qos))

    def connect(self, *args, **kwargs):
        return 0

    def loop_start(self):
        return None

    def loop_stop(self):
        return None

    def disconnect(self):
        return None


class FakeController:
    def __init__(self):
        self.calls: list[tuple] = []
        self.circuits = {}

    def get_status(self):
        return {
            "controller_state": "IDLE",
            "auto_enabled": True,
            "auto_paused": False,
        }


def test_server_discovers_device_and_marks_it_as_claimed(monkeypatch):
    store = RuntimeLiveStore()
    manager = MQTTManager()
    manager.live_store = store
    manager.client = FakeMQTTClient()

    discovered = make_envelope(
        message_type=MessageType.NODE_DISCOVERY_HELLO,
        node_id="hw-123",
        payload={
            "hardware_uid": "hw-123",
            "serial_number": "serial-abc",
            "hostname": "raspi-irrigation-0",
        },
    )

    manager._handle_discovery_hello(discovered)

    devices = store.list_discovered_devices()
    assert len(devices) == 1
    assert devices[0].hardware_uid == "hw-123"
    assert devices[0].serial_number == "serial-abc"
    assert devices[0].hostname == "raspi-irrigation-0"
    assert devices[0].node_id is None

    manager.live_store.claim_discovered_device("hw-123", node_id=7)
    devices = store.list_discovered_devices()
    assert devices[0].node_id == 7
    assert devices[0].claimed_at is not None


def test_server_assigns_node_id_and_waits_for_ack(monkeypatch):
    manager = MQTTManager()
    manager.client = FakeMQTTClient()

    original_publish = manager.client.publish

    def publish_and_ack(topic: str, payload: str, qos: int = 0):
        original_publish(topic, payload, qos)
        envelope = decode_envelope(payload)
        ack = make_envelope(
            message_type=MessageType.NODE_ASSIGNMENT_ACK,
            node_id=envelope["node_id"],
            correlation_id=envelope["message_id"],
            payload={
                "assigned_node_id": envelope["payload"]["assigned_node_id"],
                "hardware_uid": envelope["node_id"],
                "status": "stored",
            },
        )
        manager._handle_node_assignment_ack(ack)
        return FakePublishResult()

    manager.client.publish = publish_and_ack

    response = manager.publish_assign_node_id_and_wait(
        hardware_uid="hw-123",
        assigned_node_id="42",
        node_name="Backyard Node",
        timeout=1,
    )

    assert response["message_type"] == MessageType.NODE_ASSIGNMENT_ACK.value
    assert response["payload"]["assigned_node_id"] == "42"
    assert manager.client.published[0][0] == topic_discovery_command("hw-123")


def test_node_assigns_and_persists_identity(tmp_path, monkeypatch):
    identity_path = tmp_path / "node_identity.json"
    identity = NodeIdentity(hardware_uid="hw-123", assigned_node_id=None, serial_number="serial-abc", hostname="node-host")
    save_node_identity(identity, path=str(identity_path))

    monkeypatch.setattr(
        "smart_irrigation_system.node.network.mqtt_client.DEFAULT_IDENTITY_PATH",
        str(identity_path),
    )

    controller = FakeController()
    client = MQTTClient(controller, identity=load_node_identity(path=str(identity_path)), identity_path=str(identity_path))
    fake_client = FakeMQTTClient()
    client.client = fake_client

    client._on_connect(fake_client, None, None, 0)
    assert fake_client.subscriptions == [(topic_discovery_command("hw-123"), 1)]

    request = make_envelope(
        message_type=MessageType.CMD_ASSIGN_NODE_ID,
        node_id="hw-123",
        payload={
            "assigned_node_id": "7",
            "node_name": "Backyard Node",
        },
    )

    client._handle_assign_node_id(request)

    persisted = load_node_identity(path=str(identity_path))
    assert persisted.assigned_node_id == "7"
    assert client.assigned_node_id == "7"
    assert (topic_command("7"), 1) in fake_client.subscriptions
    assert ("sis/v1/nodes/7/config", 1) in fake_client.subscriptions
    assert any(topic == "sis/v1/discovery/hw-123/ack" for topic, _, _ in fake_client.published)

    client.publish_status_snapshot()
    assert fake_client.published[-1][0] == "sis/v1/nodes/7/status"
    status_envelope = decode_envelope(fake_client.published[-1][1])
    assert status_envelope["node_id"] == "7"
    assert status_envelope["message_type"] == MessageType.NODE_STATUS_SNAPSHOT.value


def test_discovery_hello_api_shape_matches_runtime_store():
    store = RuntimeLiveStore()
    store.upsert_discovered_device("hw-123", serial_number="serial-abc", hostname="node-host")
    devices = store.list_discovered_devices()

    assert len(devices) == 1
    assert devices[0].hardware_uid == "hw-123"
    assert devices[0].ever_seen is True


def test_discovery_api_returns_discovered_devices(monkeypatch):
    monkeypatch.setattr(
        "smart_irrigation_system.server.runtime.api.discovery.get_discovered_devices",
        lambda: [
            DiscoveredDeviceRead(
                hardware_uid="hw-123",
                serial_number="serial-abc",
                hostname="node-host",
                node_id=None,
                ever_seen=True,
            )
        ],
    )

    payload = list_discovered_devices()
    assert len(payload) == 1
    assert payload[0].hardware_uid == "hw-123"
    assert payload[0].serial_number == "serial-abc"


def test_server_unpairs_node_and_waits_for_ack():
    manager = MQTTManager()
    manager.client = FakeMQTTClient()

    original_publish = manager.client.publish

    def publish_and_unpair_ack(topic: str, payload: str, qos: int = 0):
        original_publish(topic, payload, qos)
        envelope = decode_envelope(payload)
        ack = make_envelope(
            message_type=MessageType.NODE_UNPAIR_ACK,
            node_id=envelope["node_id"],
            correlation_id=envelope["message_id"],
            payload={
                "hardware_uid": envelope["payload"]["hardware_uid"],
                "status": "unpaired",
            },
        )
        manager._handle_node_unpair_ack(ack)
        return FakePublishResult()

    manager.client.publish = publish_and_unpair_ack

    response = manager.publish_unpair_node_and_wait(
        node_id="5",
        hardware_uid="hw-123",
        timeout=1,
    )

    assert response["message_type"] == MessageType.NODE_UNPAIR_ACK.value
    assert response["payload"]["status"] == "unpaired"
    assert manager.client.published[0][0] == topic_command("5")


def test_node_unpair_clears_assigned_identity_and_switches_to_discovery(tmp_path):
    identity_path = tmp_path / "node_identity.json"
    save_node_identity(
        NodeIdentity(
            hardware_uid="hw-123",
            assigned_node_id="7",
            serial_number="serial-abc",
            hostname="node-host",
        ),
        path=str(identity_path),
    )

    controller = FakeController()
    client = MQTTClient(
        controller,
        identity=load_node_identity(path=str(identity_path)),
        identity_path=str(identity_path),
    )
    fake_client = FakeMQTTClient()
    client.client = fake_client

    request = make_envelope(
        message_type=MessageType.CMD_UNPAIR_NODE,
        node_id="7",
        payload={"hardware_uid": "hw-123"},
    )

    client._handle_unpair_node(request)

    persisted = load_node_identity(path=str(identity_path))
    assert persisted.assigned_node_id is None
    assert client.assigned_node_id is None
    assert (topic_command("7"), 0) in fake_client.unsubscriptions
    assert ("sis/v1/nodes/7/config", 0) in fake_client.unsubscriptions
    assert (topic_discovery_command("hw-123"), 1) in fake_client.subscriptions

    ack_topics = [topic for topic, _, _ in fake_client.published]
    assert "sis/v1/nodes/7/ack" in ack_topics
    assert topic_discovery_hello() in ack_topics