from datetime import datetime, timezone

from sqlmodel import Session

from smart_irrigation_system.server.configuration.repositories.node_repository import NodeRepository
from smart_irrigation_system.server.configuration.repositories.zone_repository import ZoneRepository
from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from sqlmodel import select
from smart_irrigation_system.server.configuration.repositories.zone_lifecycle_repository import ZoneLifecycleRepository
from smart_irrigation_system.server.configuration.models.zone_lifecycle import ZoneLifecycle
from smart_irrigation_system.server.configuration.schemas.node import NodeCreate, NodeUpdate
from smart_irrigation_system.server.configuration.schemas.zone import ZoneCreate, ZoneUpdate
from smart_irrigation_system.server.configuration.models.node import (
    CONFIG_SYNC_PENDING,
    CONFIG_SYNC_PUSHED,
)


class NodeService:
    def __init__(self, session: Session):
        self.session = session
        self.node_repo = NodeRepository(session)
        self.zone_repo = ZoneRepository(session)
        self.zone_lifecycle_repo = ZoneLifecycleRepository(session)


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
        if data.hardware_uid:
            existing = self.node_repo.get_by_hardware_uid(data.hardware_uid)
            if existing:
                raise ValueError(f"Hardware UID '{data.hardware_uid}' is already assigned to node {existing.id}")

        new_node = Node(
            name=data.name,
            location=data.location,
            hardware_uid=data.hardware_uid,
            config_sync_status=CONFIG_SYNC_PENDING,
            hardware=data.hardware.model_dump(),
            irrigation_limits=data.irrigation_limits.model_dump(),
            automation=data.automation.model_dump(),
            batch_strategy=data.batch_strategy.model_dump(),
            logging=data.logging.model_dump()
        )

        self.node_repo.create(new_node)
        self.session.commit()

        return new_node


    def get_node_by_hardware_uid(self, hardware_uid: str) -> Node | None:
        return self.node_repo.get_by_hardware_uid(hardware_uid)


    def update_node(self, node_id: int, data: NodeUpdate) -> Node | None:
        config_fields = {"hardware", "irrigation_limits", "automation", "batch_strategy", "logging"}
        
        # Build update_data by directly accessing fields and converting nested models
        update_data = {}
        
        # Add fields that are set (not None)
        if data.name is not None:
            update_data["name"] = data.name
        if data.location is not None:
            update_data["location"] = data.location
        if data.hardware is not None:
            update_data["hardware"] = data.hardware.model_dump()
        if data.irrigation_limits is not None:
            update_data["irrigation_limits"] = data.irrigation_limits.model_dump()
        if data.automation is not None:
            update_data["automation"] = data.automation.model_dump()
        if data.batch_strategy is not None:
            update_data["batch_strategy"] = data.batch_strategy.model_dump()
        if data.logging is not None:
            update_data["logging"] = data.logging.model_dump()

        if config_fields.intersection(update_data.keys()):
            update_data["config_sync_status"] = CONFIG_SYNC_PENDING

        if update_data:
            update_data["last_updated"] = datetime.now(timezone.utc)

        node = self.node_repo.update(node_id, update_data)
        if not node:
            return None

        self.session.commit()
        return node


    def update_zone(self, node_id: int, zone_id: int, data: ZoneUpdate) -> Zone | None:
        zone = self.zone_repo.get(zone_id)
        if not zone or zone.node_id != node_id:
            return None

        # Build update_data by directly accessing fields and converting nested models
        update_data = {}
        
        # Add fields that are set (not None)
        if data.name is not None:
            update_data["name"] = data.name
        if data.relay_pin is not None:
            update_data["relay_pin"] = data.relay_pin
        if data.enabled is not None:
            update_data["enabled"] = data.enabled
        if data.local_correction_factors is not None:
            update_data["local_correction_factors"] = data.local_correction_factors.model_dump()
        if data.frequency_settings is not None:
            update_data["frequency_settings"] = data.frequency_settings.model_dump()
        if data.fallback_strategy is not None:
            update_data["fallback_strategy"] = data.fallback_strategy.model_dump()
        if data.irrigation_configuration is not None:
            update_data["irrigation_configuration"] = data.irrigation_configuration.model_dump()
        if data.emitters_configuration is not None:
            update_data["emitters_configuration"] = data.emitters_configuration.model_dump()

        updated_zone = self.zone_repo.update(zone_id, update_data)
        if not updated_zone:
            return None

        self._mark_node_config_pending(node_id)

        self.session.commit()
        return updated_zone


    def delete_node(self, node_id: int) -> bool:
        """Delete a node and all its zones, marking their history as deleted."""
        zones = self.zone_repo.list_by_node(node_id)
        
        # Delete each zone (which also marks history as deleted)
        for zone in zones:
            success = self._delete_zone_impl(node_id, zone.id)
            if not success:
                return False
        
        # Delete the node
        deleted = self.node_repo.delete(node_id)
        if not deleted:
            return False
        
        self._mark_node_config_pending(node_id)
        self.session.commit()
        return True
    

    def delete_zone(self, node_id: int, zone_id: int) -> bool:
        """Delete a zone and mark its history as deleted."""
        success = self._delete_zone_impl(node_id, zone_id)
        if success:
            # _delete_zone_impl already calls commit
            self.session.commit()
        return success


    def _delete_zone_impl(self, node_id: int, zone_id: int) -> bool:
        """
        Internal implementation for zone deletion.
        Marks zone lifecycle as deleted and flags irrigation history records.
        """
        zone = self.zone_repo.get(zone_id)
        if not zone or zone.node_id != node_id:
            return False

        now = datetime.now(timezone.utc)
        
        # Mark the active zone lifecycle as deleted
        lifecycle = self.zone_lifecycle_repo.mark_deleted(node_id, zone_id, now)

        from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory

        # Mark ALL history records for this zone as deleted (from any generation)
        # Don't filter by lifecycle because history records may be from old zone generations
        history_statement = select(IrrigationHistory).where(
            IrrigationHistory.node_id == node_id,
            IrrigationHistory.circuit_id == zone_id,
        )

        history_records = self.session.exec(history_statement).all()
        
        # Mark each history record as deleted
        for history_record in history_records:
            history_record.zone_deleted = True

        # Commit the history updates before deleting the zone
        self.session.commit()

        # Now delete the zone
        deleted = self.zone_repo.delete(zone_id)
        if not deleted:
            return False

        self._mark_node_config_pending(node_id)
        
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
        self._mark_node_config_pending(node_id)
        self.session.commit()
        

        # Create lifecycle entry for this zone
        self.zone_lifecycle_repo.create(
            ZoneLifecycle(
                node_id=node_id,
                zone_id=new_zone.id,
            )
        )
        self.session.commit()
        

        return new_zone

    def mark_config_pushed(self, node_id: int) -> Node | None:
        node = self.node_repo.get(node_id)
        if not node:
            return None

        node.config_sync_status = CONFIG_SYNC_PUSHED
        node.last_updated = datetime.now(timezone.utc)
        self.session.flush()
        self.session.commit()
        return node

    def _mark_node_config_pending(self, node_id: int) -> None:
        node = self.node_repo.get(node_id)
        if not node:
            return
        node.config_sync_status = CONFIG_SYNC_PENDING
        node.last_updated = datetime.now(timezone.utc)
        self.session.flush()