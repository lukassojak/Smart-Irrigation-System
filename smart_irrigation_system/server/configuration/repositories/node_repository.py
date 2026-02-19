from sqlmodel import Session, select

from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone


class NodeRepository:
    def __init__(self, session: Session):
        self.session = session

    
    def get(self, node_id: int) -> Node | None:
        return self.session.get(Node, node_id)
    

    def list_all(self) -> list[Node]:
        return self.session.exec(select(Node)).all()
    

    def create(self, node: Node) -> Node:
        self.session.add(node)
        self.session.flush()
        return node
    

    def update(self, node_id: int, node_data: dict) -> Node | None:
        # TODO: implement update logic
        pass
    

    def delete(self, node_id: int) -> bool:
        node = self.get(node_id)
        if not node:
            return False
        self.session.delete(node)
        self.session.flush()
        return True


    # ------------------- Domain Specific Methods -------------------


    def list_zones(self, node_id: int) -> list[Zone]:
        return self.session.exec(
            select(Zone).where(Zone.node_id == node_id)
        ).all()
    

    # TODO: remove
    def add_zone(self, node_id: int, zone: Zone) -> Zone:
        node = self.get(node_id)
        if not node:
            raise ValueError("Node not found")
        zone.node_id = node_id
        self.session.add(zone)
        self.session.flush()
        return zone