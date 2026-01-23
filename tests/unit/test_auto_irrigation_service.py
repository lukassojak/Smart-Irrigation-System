import pytest

from dataclasses import dataclass
from datetime import datetime

from smart_irrigation_system.node.core.controller.auto_irrigation_service import AutoIrrigationService


# ---------------------- Fakes ----------------------

@dataclass
class FakeAutomationSettings:
    enabled: bool

@dataclass
class FakeGlobalConfig:
    automation: FakeAutomationSettings


# ---------------------- Tests ----------------------

def test_tick_does_not_trigger_when_global_automation_disabled(monkeypatch):
    # Arrange
    triggered = {"count": 0}

    def _cb():
        triggered["count"] += 1
    
    ais = AutoIrrigationService(
        global_config=FakeGlobalConfig(automation=FakeAutomationSettings(enabled=False)),
        on_auto_irrigation_demand=_cb
    )
    ais.enable_runtime()
    # Always pretend "now is the time"
    monkeypatch.setattr(ais, "_is_time_to_irrigate", lambda: True)

    # Act
    ais.tick()

    # Assert
    assert triggered["count"] == 0


def test_tick_does_not_trigger_when_runtime_disabled(monkeypatch):
    # Arrange
    triggered = {"count": 0}

    def _cb():
        triggered["count"] += 1

    ais = AutoIrrigationService(
        global_config=FakeGlobalConfig(automation=FakeAutomationSettings(enabled=True)),
        on_auto_irrigation_demand=_cb
    )
    ais.disable_runtime()
    monkeypatch.setattr(ais, "_is_time_to_irrigate", lambda: True)

    # Act
    ais.tick()

    # Assert
    assert triggered["count"] == 0


def test_enable_and_disable_runtime_affects_triggering(monkeypatch):
    # Arrange
    triggered = {"count": 0}

    def _cb():
        triggered["count"] += 1

    ais = AutoIrrigationService(
        global_config=FakeGlobalConfig(automation=FakeAutomationSettings(enabled=True)),
        on_auto_irrigation_demand=_cb
    )
    # runtime should be initially enabled
    monkeypatch.setattr(ais, "_is_time_to_irrigate", lambda: True)

    # Act & Assert

    ais.tick()
    assert triggered["count"] == 1

    ais.disable_runtime()
    ais.tick()
    assert triggered["count"] == 1  # should not have triggered

    ais.enable_runtime()
    ais.tick()
    assert triggered["count"] == 2 # should have triggered again


def test_tick_does_trigger_once(monkeypatch):
    # Arrange
    triggered = {"count": 0}

    def _cb():
        triggered["count"] += 1

    ais = AutoIrrigationService(
        global_config=FakeGlobalConfig(automation=FakeAutomationSettings(enabled=True)),
        on_auto_irrigation_demand=_cb
    )
    ais.enable_runtime()
    monkeypatch.setattr(ais, "_is_time_to_irrigate", lambda: True)

    # Act
    ais.tick()

    # Assert
    assert triggered["count"] == 1


def test_tick_does_trigger_multiple_times(monkeypatch):
    # Arrange
    triggered = {"count": 0}

    def _cb():
        triggered["count"] += 1

    ais = AutoIrrigationService(
        global_config=FakeGlobalConfig(automation=FakeAutomationSettings(enabled=True)),
        on_auto_irrigation_demand=_cb
    )
    ais.enable_runtime()
    monkeypatch.setattr(ais, "_is_time_to_irrigate", lambda: True)

    # Act
    ais.tick()
    ais.tick()
    ais.tick()

    # Assert
    assert triggered["count"] == 3


def test_tick_only_triggers_once_per_day(monkeypatch):
    # Arrange
    triggered = {"count": 0}

    def _cb():
        triggered["count"] += 1

    automation = FakeAutomationSettings(enabled=True)
    automation.scheduled_hour = 12
    automation.scheduled_minute = 0

    ais = AutoIrrigationService(
        global_config=FakeGlobalConfig(automation=automation),
        on_auto_irrigation_demand=_cb
    )
    
    # Fake the current time to 12:00 (exact trigger time)
    fake_time = datetime(2025, 1, 1, 12, 0, 0)

    monkeypatch.setattr(
        "smart_irrigation_system.node.utils.time_utils.now",
        lambda: fake_time
    )

    # Act - first tick should trigger
    ais.tick()
    assert triggered["count"] == 1

    # second tick on same day should not trigger
    ais.tick()
    assert triggered["count"] == 1