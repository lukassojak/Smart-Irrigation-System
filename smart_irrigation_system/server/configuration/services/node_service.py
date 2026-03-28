from sqlmodel import Session

from smart_irrigation_system.server.configuration.repositories.node_repository import NodeRepository
from smart_irrigation_system.server.configuration.repositories.zone_repository import ZoneRepository
from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.schemas.node import NodeCreate, NodeUpdate
from smart_irrigation_system.server.configuration.schemas.zone import ZoneCreate, ZoneUpdate


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
        update_data = data.model_dump(exclude_unset=True)

        if "hardware" in update_data and update_data["hardware"] is not None:
            update_data["hardware"] = update_data["hardware"].model_dump()
        if "irrigation_limits" in update_data and update_data["irrigation_limits"] is not None:
            update_data["irrigation_limits"] = update_data["irrigation_limits"].model_dump()
        if "automation" in update_data and update_data["automation"] is not None:
            update_data["automation"] = update_data["automation"].model_dump()
        if "batch_strategy" in update_data and update_data["batch_strategy"] is not None:
            update_data["batch_strategy"] = update_data["batch_strategy"].model_dump()
        if "logging" in update_data and update_data["logging"] is not None:
            update_data["logging"] = update_data["logging"].model_dump()

        node = self.node_repo.update(node_id, update_data)
        if not node:
            return None

        self.session.commit()
        return node


    def update_zone(self, node_id: int, zone_id: int, data: ZoneUpdate) -> Zone | None:
        zone = self.zone_repo.get(zone_id)
        if not zone or zone.node_id != node_id:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "local_correction_factors" in update_data and update_data["local_correction_factors"] is not None:
            update_data["local_correction_factors"] = update_data["local_correction_factors"].model_dump()
        if "frequency_settings" in update_data and update_data["frequency_settings"] is not None:
            update_data["frequency_settings"] = update_data["frequency_settings"].model_dump()
        if "fallback_strategy" in update_data and update_data["fallback_strategy"] is not None:
            update_data["fallback_strategy"] = update_data["fallback_strategy"].model_dump()
        if "irrigation_configuration" in update_data and update_data["irrigation_configuration"] is not None:
            update_data["irrigation_configuration"] = update_data["irrigation_configuration"].model_dump()
        if "emitters_configuration" in update_data and update_data["emitters_configuration"] is not None:
            update_data["emitters_configuration"] = update_data["emitters_configuration"].model_dump()

        updated_zone = self.zone_repo.update(zone_id, update_data)
        if not updated_zone:
            return None

        self.session.commit()
        return updated_zone


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