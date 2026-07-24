"""Tests for the irrigation history API endpoints."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from sqlmodel import SQLModel
from sqlalchemy.pool import StaticPool

from smart_irrigation_system.server.main import app, engine
from smart_irrigation_system.server.db.session import get_session
from smart_irrigation_system.server.configuration.domain.domain import IrrigationMode
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.models.zone_lifecycle import ZoneLifecycle
from smart_irrigation_system.server.configuration.services.node_service import NodeService
from smart_irrigation_system.server.runtime.models.irrigation_history import IrrigationHistory
from smart_irrigation_system.server.configuration.models.node import Node


@pytest.fixture
def test_db():
    """Create an in-memory test database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(test_db):
    """Create a test client with test database."""
    def get_session_override():
        with Session(test_db) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    return TestClient(app)


@pytest.fixture
def test_node(test_db):
    """Create a test node in the database."""
    session = Session(test_db)
    node = Node(name="Test Node", hardware_uid="test-hw-uid")
    session.add(node)
    session.commit()
    session.refresh(node)
    return node


def test_upload_history_records(client, test_node):
    """Test uploading irrigation history records."""
    payload = {
        "node_id": test_node.id,
        "records": [
            {
                "circuit_id": 1,
                "start_time": "2024-04-30T10:00:00",
                "outcome": "success",
                "was_manual_run": False,
                "success": True,
                "completed_duration": 300,
                "target_duration": 300,
                "actual_water_amount": 50.0,
                "target_water_amount": 50.0,
                "reason": None,
                "base_water_amount": 50.0,
                "standard_conditions_solar": 100.0,
                "standard_conditions_rain": 0.0,
                "standard_conditions_temp": 22.0,
                "actual_solar": 110.0,
                "actual_rain": 0.0,
                "actual_temp": 23.0,
                "carry_over_applied": False,
                "even_area_mode": True,
                "dynamic_interval_enabled": False,
                "irrigation_volume_threshold_percent": 50,
            },
            {
                "circuit_id": 2,
                "start_time": "2024-04-30T11:00:00",
                "outcome": "skipped",
                "was_manual_run": False,
                "success": True,
                "completed_duration": None,
                "target_duration": 300,
                "actual_water_amount": None,
                "target_water_amount": 50.0,
                "reason": "Insufficient water",
                "carry_over_applied": True,
            },
        ]
    }

    response = client.post("/api/v1/history/irrigation-history/upload", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["uploaded_count"] == 2
    assert "records" in data["message"].lower()


def test_upload_duplicate_records(client, test_node):
    """Test that duplicate records are skipped."""
    # First upload
    payload = {
        "node_id": test_node.id,
        "records": [
            {
                "circuit_id": 1,
                "start_time": "2024-04-30T10:00:00",
                "outcome": "success",
                "completed_duration": 300,
                "target_duration": 300,
                "actual_water_amount": 50.0,
                "target_water_amount": 50.0,
            },
        ]
    }
    response1 = client.post("/api/v1/history/irrigation-history/upload", json=payload)
    assert response1.status_code == 200
    assert response1.json()["uploaded_count"] == 1

    # Second upload (same record - should be skipped)
    response2 = client.post("/api/v1/history/irrigation-history/upload", json=payload)
    assert response2.status_code == 200
    data = response2.json()
    assert data["uploaded_count"] == 0
    assert "duplicate" in data["message"].lower()


def test_fetch_history_records(client, test_node, test_db):
    """Test fetching irrigation history records."""
    session = Session(test_db)
    zone = Zone(
        node_id=test_node.id,
        name="Zone 1",
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

    session.add_all(
        [
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=zone.id,
                zone_deleted=False,
                start_time=datetime(2024, 4, 30, 10, 0, 0),
                outcome="success",
                success=True,
                was_manual_run=False,
                completed_duration=300,
                target_duration=300,
                actual_water_amount=50.0,
                target_water_amount=50.0,
                base_water_amount=50.0,
                even_area_mode=True,
                target_mm=5.0,
                actual_mm=5.0,
            ),
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=zone.id,
                zone_deleted=False,
                start_time=datetime(2024, 4, 30, 11, 0, 0),
                outcome="success",
                success=True,
                was_manual_run=False,
                completed_duration=250,
                target_duration=300,
                actual_water_amount=42.0,
                target_water_amount=50.0,
                base_water_amount=100.0,
                even_area_mode=True,
                target_mm=5.0,
                actual_mm=4.2,
            ),
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=zone.id,
                zone_deleted=False,
                start_time=datetime(2024, 4, 30, 13, 0, 0),
                outcome="success",
                success=True,
                was_manual_run=True,
                completed_duration=120,
                target_duration=300,
                actual_water_amount=30.0,
                target_water_amount=30.0,
                base_water_amount=100.0,
            ),
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=zone.id,
                zone_deleted=False,
                start_time=datetime(2024, 4, 30, 14, 0, 0),
                outcome="success",
                success=True,
                was_manual_run=False,
                completed_duration=90,
                target_duration=300,
                actual_water_amount=20.0,
                target_water_amount=20.0,
                base_water_amount=0.0,
                even_area_mode=True,
                target_mm=5.0,
                actual_mm=4.0,
            ),
            IrrigationHistory(
                node_id=test_node.id,
                circuit_id=2,
                zone_deleted=False,
                start_time=datetime(2024, 4, 30, 12, 0, 0),
                outcome="skipped",
                success=True,
                was_manual_run=False,
                actual_water_amount=None,
                target_water_amount=50.0,
                base_water_amount=None,
                reason="Insufficient water",
            ),
        ]
    )
    session.commit()

    # Fetch all records with a low limit to verify avg_correction ignores manual and invalid base values.
    response = client.get(f"/api/v1/history/irrigation-history/records?node_id={test_node.id}&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 5
    assert data["returned_records"] == 1
    assert data["success_rate"] == pytest.approx(1.0)
    assert data["total_water"] == pytest.approx(142.0)
    assert data["avg_correction"] == pytest.approx(-0.25)
    assert data["records"][0]["success"] is True
    assert data["records"][0]["carry_over_applied"] in (True, False)

    # Fetch circuit 1 records only.
    response = client.get(
        f"/api/v1/history/irrigation-history/records?node_id={test_node.id}&circuit_id=1&limit=1"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 4
    assert data["returned_records"] == 1
    assert data["avg_correction"] == pytest.approx(-0.25)
    even_area_record = data["records"][0]
    assert even_area_record["even_area_mode"] is True
    assert even_area_record["target_mm"] == pytest.approx(5.0)
    assert even_area_record["actual_mm"] == pytest.approx(4.0)


def test_fetch_empty_history(client, test_node):
    """Test fetching history when no records exist."""
    response = client.get(f"/api/v1/history/irrigation-history/records?node_id={test_node.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 0
    assert data["returned_records"] == 0
    assert data["records"] == []
    assert data["avg_correction"] == pytest.approx(0.0)


def test_delete_zone_marks_existing_history_as_deleted(test_db, test_node):
    session = Session(test_db)
    zone = Zone(
        node_id=test_node.id,
        name="Jahody",
        relay_pin=9,
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

    lifecycle = ZoneLifecycle(
        node_id=test_node.id,
        zone_id=zone.id,
        created_at=datetime(2024, 1, 1, 10, 0, 0),
    )
    session.add(lifecycle)

    history_record = IrrigationHistory(
        node_id=test_node.id,
        circuit_id=zone.id,
        zone_deleted=False,
        start_time=datetime(2024, 1, 10, 10, 0, 0),
        outcome="success",
        success=True,
        was_manual_run=False,
        completed_duration=300,
        target_duration=300,
        actual_water_amount=50.0,
        target_water_amount=50.0,
    )
    session.add(history_record)
    persisted_node = session.get(Node, test_node.id)
    persisted_node.header_pins = {}
    session.add(persisted_node)
    session.commit()

    service = NodeService(session)
    assert service.delete_zone(test_node.id, zone.id) is True

    refreshed_history = session.exec(
        select(IrrigationHistory).where(
            IrrigationHistory.node_id == test_node.id,
            IrrigationHistory.circuit_id == zone.id,
            IrrigationHistory.start_time == datetime(2024, 1, 10, 10, 0, 0),
        )
    ).first()
    assert refreshed_history is not None
    assert refreshed_history.zone_deleted is True


def test_upload_history_respects_deleted_zone_lifecycle(client, test_node, test_db):
    session = Session(test_db)
    session.add_all([
        ZoneLifecycle(
            node_id=test_node.id,
            zone_id=9,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            deleted_at=datetime(2024, 2, 1, 10, 0, 0),
        ),
        ZoneLifecycle(
            node_id=test_node.id,
            zone_id=9,
            created_at=datetime(2024, 3, 1, 10, 0, 0),
            deleted_at=None,
        ),
    ])
    session.commit()

    payload = {
        "node_id": test_node.id,
        "records": [
            {
                "circuit_id": 9,
                "start_time": "2024-01-15T10:00:00",
                "outcome": "success",
                "was_manual_run": False,
                "success": True,
                "completed_duration": 300,
                "target_duration": 300,
                "actual_water_amount": 50.0,
                "target_water_amount": 50.0,
            },
            {
                "circuit_id": 9,
                "start_time": "2024-03-15T10:00:00",
                "outcome": "success",
                "was_manual_run": False,
                "success": True,
                "completed_duration": 280,
                "target_duration": 300,
                "actual_water_amount": 48.0,
                "target_water_amount": 50.0,
            },
        ],
    }

    response = client.post("/api/v1/history/irrigation-history/upload", json=payload)
    assert response.status_code == 200

    response = client.get(f"/api/v1/history/irrigation-history/records?node_id={test_node.id}&limit=10&include_deleted_zones=true")
    assert response.status_code == 200
    payload = response.json()
    data = payload["records"]

    assert len(data) == 2
    current_record = data[0]
    old_record = data[1]

    assert old_record["zone_deleted"] is True
    assert current_record["zone_deleted"] is False
    assert current_record["success"] is True
    assert payload["total_records"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
