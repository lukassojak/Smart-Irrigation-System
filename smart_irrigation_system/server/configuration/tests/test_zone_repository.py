from sqlmodel import SQLModel, create_engine, Session
import pytest

from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.repositories.zone_repository import ZoneRepository


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
    

def test_create_and_get_zone(session: Session):
    zone_repo = ZoneRepository(session)

    zone = Zone(
        node_id=1,
        name="Zone 1",
        relay_pin=3,
        enabled=True,
        irrigation_mode="even_area",
        irrigation_Configuration={"zone_area_m2": 10, "target_mm": 5},
        emitters_configuration={"summary": []},
    )

    zone_repo.create(zone)
    session.commit()

    loaded = zone_repo.get(zone.id)

    assert loaded is not None
    assert loaded.name == "Zone 1"


def test_list_zones_by_node(session: Session):
    zone_repo = ZoneRepository(session)

    zone_repo.create(Zone(node_id=1, name="Z1", relay_pin=1, irrigation_mode="even_area"))
    zone_repo.create(Zone(node_id=1, name="Z2", relay_pin=2, irrigation_mode="even_area"))
    zone_repo.create(Zone(node_id=2, name="Z3", relay_pin=3, irrigation_mode="per_plant"))
    session.commit()

    zones = zone_repo.list_by_node(1)
    assert len(zones) == 2


def test_update_zone(session: Session):
    repo = ZoneRepository(session)

    zone = Zone(node_id=1, name="Old", relay_pin=1, irrigation_mode="even_area")
    repo.create(zone)
    session.commit()

    updated = repo.update(zone.id, {"name": "New"})
    session.commit()

    assert updated.name == "New"