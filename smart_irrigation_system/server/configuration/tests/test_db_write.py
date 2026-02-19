from sqlmodel import Session, SQLModel, create_engine, select

from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone, IrrigationMode


engine = create_engine("sqlite:///:memory:", echo=True)
SQLModel.metadata.create_all(engine)


def test_write_node_and_zone():
    node = Node(
        name="Test Node",
        location="Garden",
        hardware={"input_pins": [2], "output_pins": [3, 4]},
        irrigation_limits={"min_percent": 30, "max_percent": 200, "main_valve_max_flow": 1500},
        automation={"enabled": True, "scheduled_hour": 6, "scheduled_minute": 0, "weather_cache_interval_minutes": 30, "weather_cache_expiry_hours": 2},
        batch_strategy={"concurrent_irrigation": True, "flow_control": True, "max_concurrent_zones": 2, "max_total_irrigation_time_minutes": 120},
        logging={"enabled": True, "log_level": "DEBUG"}
    )


    with Session(engine) as session:
        session.add(node)
        session.commit()
        session.refresh(node)

    # create zone
    zone = Zone(
        node_id=node.id,
        name="Front Lawn",
        relay_pin=3,
        irrigation_mode=IrrigationMode.EVEN_AREA,
        target_mm=10.0,
        zone_area_m2=50.0,
        base_target_volume_liters=5.0,
        local_correction_factors={
                "solar": 0.05,
                "rain": 0.1,
                "temperature": 0
            },
        frequency_settings={
                "dynamic_interval": True,
                "min_interval_days": 1,
                "max_interval_days": 7,
                "carry_over_volume": True,
                "irrigation_volume_threshold_percent": 20
            },
        fallback_strategy={
                "on_fresh_weather_data_unavailable": "use_cached_data",
                "on_expired_weather_data": "use_cached_data",
                "on_missing_weather_data": "use_base_volume"
            },
        irrigation_configuration={
                "zone_area_m2": 5.0,
                "target_mm": 6.0
            },
        emitters_configuration={
                "summary": [
                    {
                        "type": "dripper",
                        "flow_rate_lph": 4,
                        "count": 10
                    },
                    {
                        "type": "dripper",
                        "flow_rate_lph": 8,
                        "count": 5
                    }
                ]
            },
        node=node
    )

    with Session(engine) as session:
        session.add(zone)
        session.commit()
        session.refresh(zone)
    
    # test queries
    saved_nodes = session.exec(select(Node)).all()
    saved_zones = session.exec(select(Zone)).all()

    print("Saved Nodes:", saved_nodes)
    print("Saved Zones:", saved_zones)

    assert len(saved_nodes) == 1
    assert len(saved_zones) == 1

    # check relationships
    assert saved_zones[0].node.id == saved_nodes[0].id
    assert saved_nodes[0].zones[0].id == saved_zones[0].id

    # check nested JSON fields
    assert saved_nodes[0].hardware["input_pins"] == [2]
    assert saved_zones[0].local_correction_factors["rain"] == 0.1
    assert saved_zones[0].frequency_settings["dynamic_interval"] is True
    assert saved_zones[0].emitters_configuration["summary"][0]["flow_rate_lph"] == 4