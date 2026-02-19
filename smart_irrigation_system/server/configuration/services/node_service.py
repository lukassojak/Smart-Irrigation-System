from sqlmodel import Session

from smart_irrigation_system.server.configuration.repositories.node_repository import NodeRepository
from smart_irrigation_system.server.configuration.repositories.zone_repository import ZoneRepository
from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.schemas.node import NodeCreate, NodeUpdate
from smart_irrigation_system.server.configuration.schemas.zone import ZoneCreate


class NodeService:
    def __init__(self, session: Session):
        self.session = session
        self.node_repo = NodeRepository(session)
        self.zone_repo = ZoneRepository(session)


    def get_node(self, node_id: int) -> Node | None:
        """
        Retrieve a node by its ID.

        :param node_id: The ID of the node to retrieve.
        :return: The Node object if found, otherwise None.
        """
        node = self.node_repo.get(node_id)
        return node
    

    def get_zone(self, node_id: int, zone_id: int) -> Zone | None:
        zone = self.zone_repo.get(zone_id)
        if not zone or zone.node_id != node_id:
            return None
        return zone


    def list_nodes(self) -> list[Node]:
        nodes = self.node_repo.list_all()
        return nodes


    def list_zones(self, node_id: int) -> list[Zone]:
        zones = self.zone_repo.list_by_node(node_id)
        return zones
    

    def create_node(self, data: NodeCreate) -> Node:
        """
        Create a new node with the provided data.

        :param data: NodeCreate schema containing the node details.
        :return: The newly created Node object.
        :raises ValueError: If a node with the same name already exists.
        """
        new_node = Node(
            name=data.name,
            location=data.location,
            hardware=data.hardware.model_dump(),
            irrigation_limits=data.irrigation_limits.model_dump(),
            automation=data.automation.model_dump(),
            batch_strategy=data.batch_strategy.model_dump(),
            logging=data.logging.model_dump()
        )

        self.node_repo.create(new_node)
        self.session.commit()

        return new_node


    def update_node(self, node_id: int, data: NodeUpdate) -> Node | None:
        pass


    def delete_node(self, node_id: int) -> bool:
        deleted = self.node_repo.delete(node_id)
        if not deleted:
            return False
        
        self.session.commit()
        return True
    

    def delete_zone(self, node_id: int, zone_id: int) -> bool:
        zone = self.zone_repo.get(zone_id)
        if not zone or zone.node_id != node_id:
            return False
        deleted = self.zone_repo.delete(zone_id)
        if not deleted:
            return False
        
        self.session.commit()
        return True


    def add_zone_to_node(self, node_id: int, zone_data: ZoneCreate) -> Zone:
        """
        Add a new zone to the specified node.
        
        :param node_id: The ID of the node to which the zone will be added.
        :param zone_data: ZoneCreate schema containing the zone details.
        :return: The newly created Zone object.
        :raises ValueError: If the node with the specified ID does not exist.
        """
        node = self.node_repo.get(node_id)
        if not node:
            raise ValueError("Node {node_id} not found")
        
        new_zone = Zone(
            node_id=node_id,
            name=zone_data.name,
            relay_pin=zone_data.relay_pin,
            enabled=zone_data.enabled,
            irrigation_mode=zone_data.irrigation_mode,
            local_correction_factors=zone_data.local_correction_factors.model_dump(),
            frequency_settings=zone_data.frequency_settings.model_dump(),
            fallback_strategy=zone_data.fallback_strategy.model_dump(),
            irrigation_configuration=zone_data.irrigation_configuration.model_dump(),
            emitters_configuration=zone_data.emitters_configuration.model_dump()
        )

        self.zone_repo.create(new_zone)
        self.session.commit()
        

        return new_zone