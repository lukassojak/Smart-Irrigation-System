from sqlmodel import Session, select

from smart_irrigation_system.server.configuration.models.zone import Zone


class ZoneRepository:
    def __init__(self, session: Session):
        self.session = session

    
    def get(self, zone_id: int) -> Zone | None:
        return self.session.get(Zone, zone_id)

    
    def list_by_node(self, node_id: int) -> list[Zone]:
        return self.session.exec(select(Zone).where(Zone.node_id == node_id)).all()


    def create(self, zone: Zone) -> Zone:
        self.session.add(zone)
        self.session.flush()
        return zone


    def update(self, zone_id: int, data: dict) -> Zone | None:
        # Validation should be done by service layer
        zone = self.get(zone_id)
        if not zone:
            return None

        for key, value in data.items():
            setattr(zone, key, value)

        self.session.flush()
        return zone


    def delete(self, zone_id: int) -> bool:
        zone = self.get(zone_id)
        if not zone:
            return False
        self.session.delete(zone)
        self.session.flush()
        return True