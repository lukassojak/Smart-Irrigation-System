from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DiscoveredDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hardware_uid: str
    serial_number: str | None = None
    hostname: str | None = None
    node_id: int | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    claimed_at: datetime | None = None
    ever_seen: bool = False