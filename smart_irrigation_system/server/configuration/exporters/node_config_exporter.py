from datetime import datetime, timezone

from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone
from smart_irrigation_system.server.configuration.models.global_config import GlobalConfig
from smart_irrigation_system.server.configuration.domain.domain import IrrigationMode

# TEMPORARY HOTFIX:
# Server currently stores Raspberry Pi physical header numbering,
# while node runtime expects BCM numbering.
# TODO: Replace by explicit relay_pin_physical/relay_pin_bcm fields.

PHYSICAL_TO_BCM = {
    3: 2,
    5: 3,
    7: 4,
    8: 14,
    10: 15,
    11: 17,
    12: 18,
    13: 27,
    15: 22,
    16: 23,
    18: 24,
    19: 10,
    21: 9,
    22: 25,
    23: 11,
    24: 8,
    26: 7,
    27: 0,
    28: 1,
    29: 5,
    31: 6,
    32: 12,
    33: 13,
    35: 19,
    36: 16,
    37: 26,
    38: 20,
    40: 21,
}

def _physical_to_bcm(pin: int | None) -> int | None:
    if pin is None:
        return None

    bcm = PHYSICAL_TO_BCM.get(pin)
    if bcm is None:
        raise ValueError(
            f"Physical GPIO pin {pin} cannot be mapped to BCM numbering."
        )

    return bcm

def export_node_config(node: Node) -> dict:
    """
    Export the configuration of a Node as a dictionary for direct use in SIS.

    :param node: The Node object to export.
    :return: A dictionary representing the node's configuration.
    """
    node_config = {
        "metadata": {
            "version": node.version,
            "last_updated": node.last_updated.replace(microsecond=0).isoformat(),
            "exported_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        },
        "node_id": node.id,
        "name": node.name,
        "location": node.location,
        "hardware": node.hardware,
        "irrigation_limits": node.irrigation_limits,
        "automation": node.automation,
        "batch_strategy": node.batch_strategy,
        "logging": node.logging,
        "zones": [_get_zone_config(zone) for zone in node.zones],
    }
    return node_config


def _get_zone_config(zone: Zone) -> dict:
    zone_config = {
        "id": zone.id,
        "name": zone.name,
        "relay_pin": _physical_to_bcm(zone.relay_pin),
        "enabled": zone.enabled,
        "irrigation_mode": zone.irrigation_mode.value,
        "local_correction_factors": zone.local_correction_factors,
        "frequency_settings": zone.frequency_settings,
        "fallback_strategy": zone.fallback_strategy,
        "irrigation_configuration": zone.irrigation_configuration,
        "emitters_configuration": zone.emitters_configuration,
    }
    return zone_config


def export_node_legacy_runtime_config(node: Node, global_config: GlobalConfig | None = None) -> dict:
    """
    Export config in the current node runtime file format.

    Returns a payload equivalent to two files used by node:
    - config_global.json
    - zones_config.json
    """
    return {
        "config_global": _to_legacy_global_config(node, global_config),
        "zones_config": {
            "zones": [_to_legacy_zone_config(zone) for zone in node.zones]
        },
    }


def _to_legacy_global_config(node: Node, global_config: GlobalConfig | None = None) -> dict:
    irrigation_limits = node.irrigation_limits or {}
    automation = node.automation or {}
    logging = node.logging or {}
    batch_strategy = node.batch_strategy or {}

    default_standard_conditions = {
        "solar_total": 5.5,
        "rain_mm": 0.0,
        "temperature_celsius": 15.0,
    }
    default_correction_factors = {
        "solar": 0.0,
        "rain": 0.0,
        "temperature": 0.0,
    }
    default_weather_api = {
        "api_enabled": True,
        "realtime_url": "https://api.ecowitt.net/api/v3/device/real_time",
        "history_url": "https://api.ecowitt.net/api/v3/device/history",
        "api_key": None,
        "application_key": None,
        "device_mac": None,
    }

    persisted_standard_conditions = (global_config.standard_conditions if global_config else None) or {}
    persisted_correction_factors = (global_config.correction_factors if global_config else None) or {}
    persisted_weather_api = (global_config.weather_api if global_config else None) or {}

    standard_conditions = {
        "solar_total": _to_float_or_default(
            persisted_standard_conditions.get("solar_total"),
            default_standard_conditions["solar_total"],
        ),
        "rain_mm": _to_float_or_default(
            persisted_standard_conditions.get("rain_mm"),
            default_standard_conditions["rain_mm"],
        ),
        "temperature_celsius": _to_float_or_default(
            persisted_standard_conditions.get("temperature_celsius"),
            default_standard_conditions["temperature_celsius"],
        ),
    }

    correction_factors = {
        "solar": _to_float_or_default(
            persisted_correction_factors.get("solar"),
            default_correction_factors["solar"],
        ),
        "rain": _to_float_or_default(
            persisted_correction_factors.get("rain"),
            default_correction_factors["rain"],
        ),
        "temperature": _to_float_or_default(
            persisted_correction_factors.get("temperature"),
            default_correction_factors["temperature"],
        ),
    }

    weather_api = {
        "api_enabled": bool(persisted_weather_api.get("api_enabled", default_weather_api["api_enabled"])),
        "realtime_url": str(persisted_weather_api.get("realtime_url", default_weather_api["realtime_url"])),
        "history_url": str(persisted_weather_api.get("history_url", default_weather_api["history_url"])),
        "api_key": persisted_weather_api.get("api_key"),
        "application_key": persisted_weather_api.get("application_key"),
        "device_mac": persisted_weather_api.get("device_mac"),
    }

    # TODO: Make node ip and port configurable in the UI, and include them in the export. For now we keep them hardcoded in the node runtime

    # Keep defaults explicit for backward compatibility with current node loader.
    return {
        "standard_conditions": standard_conditions,
        "correction_factors": correction_factors,
        "irrigation_limits": {
            "min_percent": int(irrigation_limits.get("min_percent", 0)),
            "max_percent": int(irrigation_limits.get("max_percent", 200)),
            "main_valve_max_flow": None if irrigation_limits.get("main_valve_max_flow", 850) is None else int(irrigation_limits.get("main_valve_max_flow", 850)),
        },
        "automation": {
            "enabled": bool(automation.get("enabled", True)),
            "sequential": bool(batch_strategy.get("concurrent_irrigation", False)),
            "scheduled_hour": int(automation.get("scheduled_hour", 6)),
            "scheduled_minute": int(automation.get("scheduled_minute", 0)),
            "max_flow_monitoring": bool(automation.get("max_flow_monitoring", False)),
            "environment": "development",  # This is not currently supported in the UI, so we set it to "development" for all exports
            "use_weathersimulator": False,  # This is not currently supported in the UI, so we set it to False for all exports
        },
        "logging": {
            "enabled": bool(logging.get("enabled", True)),
            "log_level": str(logging.get("log_level", "INFO")),
        },
        "weather_api": weather_api,
    }


def _to_legacy_zone_config(zone: Zone) -> dict:
    irrigation_configuration = zone.irrigation_configuration or {}
    frequency_settings = zone.frequency_settings or {}

    even_area_mode = zone.irrigation_mode == IrrigationMode.EVEN_AREA

    drippers_summary = _build_drippers_summary(zone.emitters_configuration or {})

    if even_area_mode:
        target_mm = _to_float_or_default(irrigation_configuration.get("target_mm"), 0.0)
        zone_area_m2 = _to_float_or_default(irrigation_configuration.get("zone_area_m2"), 0.0)
        liters_per_minimum_dripper = None
    else:
        # For non-even area mode, we calculate liters per minimum dripper based on the drippers summary and base target volume.
        entries = [
            (float(flow), count)
            for flow, count in drippers_summary.items()
        ]
        total_consumption = sum(flow * count for flow, count in entries)
        min_flow = min(flow for flow, _ in entries)
        base_target_volume = _to_float_or_default(
            irrigation_configuration.get("base_target_volume_liters"),
            0.0,
        )
        if total_consumption > 0 and min_flow > 0:
            liters_per_minimum_dripper = (
                base_target_volume * min_flow / total_consumption
            )
        else:
            liters_per_minimum_dripper = 0.0

        target_mm = None
        zone_area_m2 = None

    return {
        "id": zone.id,
        "name": zone.name,
        "relay_pin": _physical_to_bcm(zone.relay_pin),
        "enabled": zone.enabled,
        "even_area_mode": even_area_mode,
        "target_mm": target_mm,
        "zone_area_m2": zone_area_m2,
        "liters_per_minimum_dripper": liters_per_minimum_dripper,
        "interval_days": int(frequency_settings.get("min_interval_days", 1)),
        "frequency_settings": {
            "dynamic_interval": bool(frequency_settings.get("dynamic_interval", False)),
            "min_interval_days": int(frequency_settings.get("min_interval_days", 1)),
            "max_interval_days": int(frequency_settings.get("max_interval_days", frequency_settings.get("min_interval_days", 1))),
            "carry_over_volume": bool(frequency_settings.get("carry_over_volume", False)),
            "irrigation_volume_threshold_percent": int(frequency_settings.get("irrigation_volume_threshold_percent", 100)),
        },
        "drippers_summary": drippers_summary,
        "local_correction_factors": {
            "solar": _to_float_or_default((zone.local_correction_factors or {}).get("solar"), 0.0),
            "rain": _to_float_or_default((zone.local_correction_factors or {}).get("rain"), 0.0),
            "temperature": _to_float_or_default((zone.local_correction_factors or {}).get("temperature"), 0.0),
        },
    }


def _build_drippers_summary(emitters_configuration: dict) -> dict:
    summary: dict[str, int] = {}

    # EVEN_AREA format
    for emitter in emitters_configuration.get("summary", []):
        _accumulate_emitter(summary, emitter)

    # PER_PLANT format
    for plant in emitters_configuration.get("plants", []):
        for emitter in plant.get("emitters", []):
            _accumulate_emitter(summary, emitter)

    return summary


def _accumulate_emitter(summary: dict[str, int], emitter: dict) -> None:
    flow_rate = emitter.get("flow_rate_lph")
    count = emitter.get("count", 0)
    if flow_rate is None:
        return

    flow_key = str(int(float(flow_rate)))
    summary[flow_key] = summary.get(flow_key, 0) + int(count)


def _to_float_or_default(value, default: float) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default