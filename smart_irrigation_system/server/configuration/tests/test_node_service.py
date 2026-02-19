from sqlmodel import SQLModel, create_engine, Session, select
from pytest import fixture, raises

from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.schemas.node import NodeCreate
from smart_irrigation_system.server.configuration.schemas.zone import ZoneCreate
from smart_irrigation_system.server.configuration.services.node_service import NodeService
from smart_irrigation_system.server.configuration.domain.domain import IrrigationMode


@fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@fixture
def node_data():
    return NodeCreate(
        name="Test Node",
        location="Garden",
        hardware={"input_pins": {"pins": [1]}, "output_pins": {"pins": [2]}},
        irrigation_limits={"min_percent": 30, "max_percent": 100, "main_valve_max_flow": 840},
        automation={"enabled": True, "scheduled_hour": 20, "scheduled_minute": 0, "weather_cache_interval_minutes": 30, "weather_cache_expiry_hours": 2},
        batch_strategy={"concurrent_irrigation": False, "flow_control": True, "max_concurrent_zones": 2, "max_total_irrigation_time_minutes": 120},
        logging={"enabled": True, "log_level": "DEBUG"}
    )

@fixture
def zone_data():
    return ZoneCreate(
        name="Front Yard",
        relay_pin=3,
        enabled=True,
        irrigation_mode=IrrigationMode.EVEN_AREA,
        local_correction_factors={"solar": 1.0, "rain": 1.0, "temperature": 1.0},
        frequency_settings={
            "dynamic_interval": True,
            "min_interval_days": 2,
            "max_interval_days": 7,
            "carry_over_volume": True,
            "irrigation_volume_threshold_percent": 20,},
        fallback_strategy={
            "on_fresh_weather_data_unavailable": "use_base_volume",
            "on_expired_weather_data": "use_half_base_volume",
            "on_missing_weather_data": "skip_irrigation",
        },
        irrigation_configuration={
            "zone_area_m2": 50.0,
            "target_mm": 10.0,
        },
        emitters_configuration={
            "summary": [
                {"type": "dripper", "flow_rate_lph": 2.0, "count": 10},
                {"type": "soaker_hose", "flow_rate_lph": 4.0, "count": 5}
            ]
        }
    )


def test_create_node(session: Session, node_data: NodeCreate):
    service = NodeService(session)

    new_node: Node = service.create_node(node_data)
    # commit should be called inside create_node
    assert new_node.id == 1
    assert new_node.name == "Test Node"
    assert new_node.location == "Garden"
    assert new_node.hardware == {"input_pins": {"pins": [1]}, "output_pins": {"pins": [2]}}
    assert new_node.logging == {"enabled": True, "log_level": "DEBUG"}


def test_add_zone_to_node(session: Session, node_data: NodeCreate, zone_data: ZoneCreate):
    service = NodeService(session)

    service.create_node(node_data)

    new_zone: Zone = service.add_zone_to_node(1, zone_data)
    assert new_zone.id == 1
    assert new_zone.node_id == 1
    assert new_zone.name == "Front Yard"
    assert new_zone.relay_pin == 3
    assert new_zone.enabled is True
    assert new_zone.irrigation_mode == IrrigationMode.EVEN_AREA
    assert new_zone.local_correction_factors == {"solar": 1.0, "rain": 1.0, "temperature": 1.0}
    assert new_zone.frequency_settings == {
        "dynamic_interval": True,
        "min_interval_days": 2,
        "max_interval_days": 7,
        "carry_over_volume": True,
        "irrigation_volume_threshold_percent": 20,
    }


def test_add_zone_to_nonexistent_node(session: Session, node_data: NodeCreate, zone_data: ZoneCreate):
    service = NodeService(session)

    service.create_node(node_data)

    with raises(ValueError):
        service.add_zone_to_node(999, zone_data)
    
    # DB should remain unchanged
    nodes = session.exec(select(Node)).all()
    assert len(nodes) == 1
    zones = session.exec(select(Zone)).all()
    assert len(zones) == 0