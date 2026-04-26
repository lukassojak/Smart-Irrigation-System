from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
import json
import os
from pathlib import Path
import socket
from uuid import uuid4


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
DEFAULT_IDENTITY_PATH = os.path.join(BASE_DIR, "runtime/node/config/node_identity.json")


@dataclass
class NodeIdentity:
    hardware_uid: str
    assigned_node_id: str | None = None
    serial_number: str | None = None
    hostname: str | None = None


def _read_cpu_serial() -> str | None:
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("Serial"):
                    _, value = line.split(":", 1)
                    serial = value.strip()
                    return serial or None
    except OSError:
        return None
    return None


def _read_machine_id() -> str | None:
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            with open(path, "r", encoding="utf-8") as file:
                value = file.read().strip()
                if value:
                    return value
        except OSError:
            continue
    return None


def _generate_hardware_uid() -> tuple[str, str | None]:
    serial = _read_cpu_serial()
    if serial:
        return serial, serial

    machine_id = _read_machine_id()
    if machine_id:
        return f"uid-{sha1(machine_id.encode('utf-8')).hexdigest()[:16]}", None

    return f"uid-{uuid4().hex[:16]}", None


def _identity_to_dict(identity: NodeIdentity) -> dict[str, str | None]:
    return {
        "hardware_uid": identity.hardware_uid,
        "assigned_node_id": identity.assigned_node_id,
        "serial_number": identity.serial_number,
        "hostname": identity.hostname,
    }


def save_node_identity(identity: NodeIdentity, path: str = DEFAULT_IDENTITY_PATH) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path_obj.with_suffix(path_obj.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(_identity_to_dict(identity), file, ensure_ascii=False, indent=4)
    os.replace(temp_path, path_obj)


def load_node_identity(path: str = DEFAULT_IDENTITY_PATH) -> NodeIdentity:
    hostname = socket.gethostname()
    path_obj = Path(path)

    if path_obj.exists():
        with open(path_obj, "r", encoding="utf-8") as file:
            raw = json.load(file)

        hardware_uid = str(raw.get("hardware_uid") or "").strip()
        serial_number = raw.get("serial_number")
        assigned_node_id = raw.get("assigned_node_id")

        if not hardware_uid:
            hardware_uid, derived_serial = _generate_hardware_uid()
            serial_number = serial_number or derived_serial
            identity = NodeIdentity(
                hardware_uid=hardware_uid,
                assigned_node_id=assigned_node_id,
                serial_number=serial_number,
                hostname=raw.get("hostname") or hostname,
            )
            save_node_identity(identity, path)
            return identity

        return NodeIdentity(
            hardware_uid=hardware_uid,
            assigned_node_id=assigned_node_id,
            serial_number=serial_number,
            hostname=raw.get("hostname") or hostname,
        )

    hardware_uid, serial_number = _generate_hardware_uid()
    identity = NodeIdentity(
        hardware_uid=hardware_uid,
        assigned_node_id=None,
        serial_number=serial_number,
        hostname=hostname,
    )
    save_node_identity(identity, path)
    return identity