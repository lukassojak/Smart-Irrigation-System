import pytest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

from smart_irrigation_system.server.main import app
from smart_irrigation_system.server.db.session import get_session
from smart_irrigation_system.server.configuration.domain.domain import IrrigationMode
from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(test_db):
    def get_session_override():
        with Session(test_db) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    return TestClient(app)


@pytest.fixture
def test_node(test_db):
    with Session(test_db) as session:
        node = Node(name="Stats Node", hardware_uid="stats-hw-uid")
        session.add(node)
        session.commit()
        session.refresh(node)
        return node


@pytest.fixture
def test_zone(test_db, test_node):
    with Session(test_db) as session:
        zone = Zone(
            node_id=test_node.id,
            name="Stats Zone",
            relay_pin=5,
            enabled=True,
            irrigation_mode=IrrigationMode.EVEN_AREA,
            local_correction_factors={"solar": 0.0, "rain": 0.0, "temperature": 0.0},
            frequency_settings={"dynamic_interval": False, "min_interval_days": 1, "max_interval_days": 1, "carry_over_volume": False, "irrigation_volume_threshold_percent": 50},
            fallback_strategy={"on_fresh_weather_data_unavailable": "use_base_volume", "on_expired_weather_data": "use_base_volume", "on_missing_weather_data": "skip_irrigation"},
            irrigation_configuration={"zone_area_m2": 10.0, "target_mm": 5.0},
            emitters_configuration={"summary": []},
        )
        session.add(zone)
        session.commit()
        session.refresh(zone)
        return zone


def test_statistics_overview_and_trend(client, test_db, test_node, test_zone):
    now = datetime.utcnow()
    with Session(test_db) as session:
        session.add_all([
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=test_zone.id,
                zone_deleted=False,
                start_time=now - timedelta(days=2),
                outcome="success",
                success=True,
                was_manual_run=False,
                completed_duration=300,
                target_duration=300,
                actual_water_amount=50.0,
                target_water_amount=50.0,
                base_water_amount=100.0,
            ),
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=test_zone.id,
                zone_deleted=False,
                start_time=now - timedelta(days=1),
                outcome="failed",
                success=False,
                was_manual_run=False,
                completed_duration=120,
                target_duration=300,
                actual_water_amount=20.0,
                target_water_amount=20.0,
                base_water_amount=40.0,
            ),
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=test_zone.id,
                zone_deleted=False,
                start_time=now,
                outcome="success",
                success=True,
                was_manual_run=True,
                completed_duration=180,
                target_duration=300,
                actual_water_amount=30.0,
                target_water_amount=30.0,
                base_water_amount=60.0,
            ),
        ])
        session.commit()

    overview_response = client.get(f"/api/v1/history/statistics/overview?node_id={test_node.id}&range_days=30")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["irrigation_runs"] == 3
    assert overview["total_water"] == pytest.approx(100.0)
    assert overview["manual_runs"] == 1
    assert overview["auto_runs"] == 2
    assert overview["success_rate"] == pytest.approx(2 / 3)
    assert overview["avg_correction"] == pytest.approx(-0.5)

    trend_response = client.get(f"/api/v1/history/statistics/water-usage-trend?node_id={test_node.id}&range_days=30")
    assert trend_response.status_code == 200
    trend = trend_response.json()
    assert trend["range_days"] == 30
    assert trend["total_water"] == pytest.approx(100.0)
    assert len(trend["points"]) == 30
    assert sum(point["water"] for point in trend["points"]) == pytest.approx(100.0)
    assert len([point for point in trend["points"] if point["water"] > 0]) == 3

    trend_7d_response = client.get(f"/api/v1/history/statistics/water-usage-trend?node_id={test_node.id}&range_days=7")
    assert trend_7d_response.status_code == 200
    trend_7d = trend_7d_response.json()
    assert trend_7d["range_days"] == 7
    assert len(trend_7d["points"]) == 7
    assert sum(point["water"] for point in trend_7d["points"]) == pytest.approx(100.0)


def test_statistics_zone_panels_with_filters(client, test_db, test_node):
    with Session(test_db) as session:
        zone_a = Zone(
            node_id=test_node.id,
            name="North Lawn",
            relay_pin=5,
            enabled=True,
            irrigation_mode=IrrigationMode.EVEN_AREA,
            local_correction_factors={"solar": 0.0, "rain": 0.0, "temperature": 0.0},
            frequency_settings={"dynamic_interval": False, "min_interval_days": 1, "max_interval_days": 1, "carry_over_volume": False, "irrigation_volume_threshold_percent": 50},
            fallback_strategy={"on_fresh_weather_data_unavailable": "use_base_volume", "on_expired_weather_data": "use_base_volume", "on_missing_weather_data": "skip_irrigation"},
            irrigation_configuration={"zone_area_m2": 10.0, "target_mm": 5.0},
            emitters_configuration={"summary": []},
        )
        zone_b = Zone(
            node_id=test_node.id,
            name="Greenhouse",
            relay_pin=6,
            enabled=True,
            irrigation_mode=IrrigationMode.EVEN_AREA,
            local_correction_factors={"solar": 0.0, "rain": 0.0, "temperature": 0.0},
            frequency_settings={"dynamic_interval": False, "min_interval_days": 1, "max_interval_days": 1, "carry_over_volume": False, "irrigation_volume_threshold_percent": 50},
            fallback_strategy={"on_fresh_weather_data_unavailable": "use_base_volume", "on_expired_weather_data": "use_base_volume", "on_missing_weather_data": "skip_irrigation"},
            irrigation_configuration={"zone_area_m2": 10.0, "target_mm": 5.0},
            emitters_configuration={"summary": []},
        )
        session.add_all([zone_a, zone_b])
        session.commit()
        session.refresh(zone_a)
        session.refresh(zone_b)

        now = datetime.utcnow()
        session.add_all([
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=zone_a.id,
                zone_deleted=False,
                start_time=now - timedelta(days=2),
                outcome="success",
                success=True,
                was_manual_run=False,
                completed_duration=300,
                target_duration=300,
                actual_water_amount=50.0,
                target_water_amount=50.0,
                base_water_amount=100.0,
            ),
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=zone_a.id,
                zone_deleted=False,
                start_time=now - timedelta(days=1),
                outcome="failed",
                success=False,
                was_manual_run=False,
                completed_duration=120,
                target_duration=300,
                actual_water_amount=20.0,
                target_water_amount=20.0,
                base_water_amount=40.0,
            ),
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=zone_b.id,
                zone_deleted=False,
                start_time=now,
                outcome="stopped",
                success=False,
                was_manual_run=False,
                completed_duration=180,
                target_duration=300,
                actual_water_amount=30.0,
                target_water_amount=30.0,
                base_water_amount=60.0,
            ),
        ])
        session.commit()

    outcome_response = client.get(f"/api/v1/history/statistics/outcome-breakdown?node_id={test_node.id}&range_days=30")
    assert outcome_response.status_code == 200
    outcome = outcome_response.json()
    assert outcome["total_records"] == 3
    assert {item["name"] for item in outcome["items"]} == {"success", "failed", "stopped"}

    filtered_outcome = client.get(
        f"/api/v1/history/statistics/outcome-breakdown?node_id={test_node.id}&range_days=30&circuit_ids=1&circuit_ids=2"
    )
    assert filtered_outcome.status_code == 200
    assert filtered_outcome.json()["total_records"] == 3

    correction_response = client.get(f"/api/v1/history/statistics/zone-correction-trend?node_id={test_node.id}&circuit_id=1&range_days=30")
    assert correction_response.status_code == 200
    correction = correction_response.json()
    assert correction["zone_id"] == 1
    assert correction["points"]
    assert correction["avg_correction"] == pytest.approx(-0.5)

    distribution_response = client.get(
        f"/api/v1/history/statistics/zone-water-distribution?node_id={test_node.id}&range_days=30&circuit_ids=1&circuit_ids=2"
    )
    assert distribution_response.status_code == 200
    distribution = distribution_response.json()
    assert distribution["total_water"] == pytest.approx(100.0)
    assert len(distribution["items"]) == 2
