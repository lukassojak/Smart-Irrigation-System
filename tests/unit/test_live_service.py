from smart_irrigation_system.server.runtime.schemas.live import ZoneStatus
from smart_irrigation_system.server.runtime.services.live_service import LiveService
from smart_irrigation_system.server.runtime.state.live_store import RuntimeLiveStore


def test_zone_without_runtime_report_stays_offline_even_when_node_is_online():
    store = RuntimeLiveStore()
    store.register_expected_topology(
        [
            {
                "node_id": 1,
                "node_name": "Node 1",
                "zones": [
                    {
                        "zone_id": 10,
                        "zone_name": "Zone 10",
                        "enabled": True,
                    }
                ],
            }
        ]
    )

    # Node heartbeat arrived, but zone runtime state was never published.
    store.upsert_node_heartbeat(node_id=1)

    service = LiveService(store=store)
    response = service.get_live_snapshot()

    assert len(response.zones) == 1
    zone = response.zones[0]
    assert zone.status == ZoneStatus.OFFLINE
    assert zone.online is False


def test_zone_online_when_runtime_state_is_reported():
    store = RuntimeLiveStore()
    store.register_expected_topology(
        [
            {
                "node_id": 1,
                "node_name": "Node 1",
                "zones": [
                    {
                        "zone_id": 10,
                        "zone_name": "Zone 10",
                        "enabled": True,
                    }
                ],
            }
        ]
    )

    store.upsert_zone_state(
        node_id=1,
        zone_id=10,
        status=ZoneStatus.IDLE,
        progress_percent=0.0,
        zone_name="Zone 10",
        enabled=True,
    )

    service = LiveService(store=store)
    response = service.get_live_snapshot()

    assert len(response.zones) == 1
    zone = response.zones[0]
    assert zone.status == ZoneStatus.IDLE
    assert zone.online is True
