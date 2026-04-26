from sqlmodel import Session, select

from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.db.session import engine


class NodeTopologyService:
    def get_node_for_zone(self, zone_id: int) -> str | None:
        with Session(engine) as session:
            zone = session.get(Zone, zone_id)
            if not zone:
                return None
            return str(zone.node_id)

    def get_all_node_ids(self) -> list[str]:
        with Session(engine) as session:
            nodes = session.exec(select(Node.id)).all()
            return [str(node_id) for node_id in nodes if node_id is not None]

    def get_node_for_hardware_uid(self, hardware_uid: str) -> Node | None:
        with Session(engine) as session:
            return session.exec(select(Node).where(Node.hardware_uid == hardware_uid)).first()