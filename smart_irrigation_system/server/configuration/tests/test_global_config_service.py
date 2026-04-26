from sqlmodel import SQLModel, Session, create_engine, select

from smart_irrigation_system.server.configuration.models.node import Node, CONFIG_SYNC_PENDING
from smart_irrigation_system.server.configuration.exporters.node_config_exporter import export_node_legacy_runtime_config
from smart_irrigation_system.server.configuration.schemas.global_config import GlobalConfigUpdate
from smart_irrigation_system.server.configuration.services.global_config_service import GlobalConfigService


def _create_session() -> Session:
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_get_or_create_global_config_uses_defaults():
    with _create_session() as session:
        service = GlobalConfigService(session)
        config = service.get_or_create()

        assert config.id is not None
        assert config.standard_conditions["solar_total"] == 5.5
        assert "realtime_url" in config.weather_api


def test_update_global_config_updates_values():
    with _create_session() as session:
        service = GlobalConfigService(session)
        service.get_or_create()

        updated = service.update(
            GlobalConfigUpdate(
                standard_conditions={
                    "solar_total": 8.5,
                    "rain_mm": 0.2,
                    "temperature_celsius": 19.0,
                },
                correction_factors={
                    "solar": 0.6,
                    "rain": -0.3,
                    "temperature": 0.1,
                },
                weather_api={
                    "api_enabled": False,
                    "realtime_url": "https://example.test/realtime",
                    "history_url": "https://example.test/history",
                    "api_key": "k",
                    "application_key": "a",
                    "device_mac": "00:11:22:33:44:55",
                },
            )
        )

        assert updated.standard_conditions["solar_total"] == 8.5
        assert updated.correction_factors["rain"] == -0.3
        assert updated.weather_api["api_enabled"] is False


def test_export_legacy_uses_persisted_global_config_values():
    with _create_session() as session:
        global_service = GlobalConfigService(session)
        config = global_service.update(
            GlobalConfigUpdate(
                standard_conditions={
                    "solar_total": 9.1,
                    "rain_mm": 1.2,
                    "temperature_celsius": 21.0,
                },
                correction_factors={
                    "solar": 0.7,
                    "rain": -0.1,
                    "temperature": 0.2,
                },
                weather_api={
                    "api_enabled": True,
                    "realtime_url": "https://example.test/realtime",
                    "history_url": "https://example.test/history",
                    "api_key": None,
                    "application_key": None,
                    "device_mac": None,
                },
            )
        )

        node = Node(name="N1")
        session.add(node)
        session.commit()
        session.refresh(node)

        payload = export_node_legacy_runtime_config(node, config)

        assert payload["config_global"]["standard_conditions"]["solar_total"] == 9.1
        assert payload["config_global"]["correction_factors"]["solar"] == 0.7
        assert payload["config_global"]["weather_api"]["history_url"] == "https://example.test/history"


def test_update_global_config_marks_all_nodes_as_pending():
    with _create_session() as session:
        # Create a few nodes first
        node1 = Node(name="N1")
        node2 = Node(name="N2")
        session.add(node1)
        session.add(node2)
        session.commit()

        # Verify nodes are in initial state
        nodes = session.exec(select(Node)).all()
        assert len(nodes) == 2
        for node in nodes:
            assert node.config_sync_status == "PENDING"  # default

        # Now update global config
        service = GlobalConfigService(session)
        service.update(
            GlobalConfigUpdate(
                standard_conditions={
                    "solar_total": 10.0,
                    "rain_mm": 0.5,
                    "temperature_celsius": 20.0,
                },
            )
        )

        # Verify all nodes are marked as PENDING
        nodes = session.exec(select(Node)).all()
        for node in nodes:
            assert node.config_sync_status == CONFIG_SYNC_PENDING
