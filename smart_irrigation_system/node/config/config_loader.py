import json
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.node.config.global_config import CorrectionFactors
from smart_irrigation_system.node.config.zone_config import ZoneConfig, FrequencySettings
from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.utils.logger import get_logger
from typing import Any, Tuple, List

# Initialize logger
logger = get_logger("config_loader")



def load_global_config(filepath: str, secrets_path: str) -> GlobalConfig:
    """Loads global configuration from JSON file and secrets from environment variables or secrets file."""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        # Return a default config with API disabled if file is not found, but log a warning
        logger.warning(f"Global config file not found at path: {filepath}. Using default config.")
        data = {
            "standard_conditions": {
                "solar_total": 2000.0,
                "rain_mm": 0.0,
                "temperature_celsius": 15.0
            },
            "correction_factors": {
                "solar": 0.0,
                "rain": 0.0,
                "temperature": 0.0
            },
            "irrigation_limits": {
                "min_percent": 10,
                "max_percent": 100,
                "main_valve_max_flow": None
            },
            "automation": {
                "enabled": False,
                "sequential": True,
                "scheduled_hour": 18,
                "scheduled_minute": 0,
                "max_flow_monitoring": False,
                "environment": "development",
                "use_weathersimulator": False
            },
            "logging": {
                "enabled": True,
                "log_level": "INFO"
            },
            "weather_api": {
                "api_enabled": False,
                "realtime_url": "",
                "history_url": "",
                "api_key": "",
                "application_key": "",
                "device_mac": ""
            }
        }

    return _global_config_from_dict(data, secrets_path)


def validate_legacy_runtime_config(
    legacy_runtime_config: dict[str, Any],
    secrets_path: str,
) -> tuple[GlobalConfig, list[IrrigationCircuit]]:
    """
    Strictly validates legacy runtime config payload and builds runtime objects.

    :param legacy_runtime_config: Expected object with keys "config_global" and "zones_config".
    :param secrets_path: Path to node secrets file used to enrich weather API keys.
    :return: Tuple (GlobalConfig, list[IrrigationCircuit]) ready for runtime use.
    :raises ValueError: if payload structure or content is invalid.
    """
    if not isinstance(legacy_runtime_config, dict):
        raise ValueError("legacy_runtime_config must be an object")

    config_global = legacy_runtime_config.get("config_global")
    zones_config = legacy_runtime_config.get("zones_config")
    if not isinstance(config_global, dict) or not isinstance(zones_config, dict):
        raise ValueError("legacy_runtime_config must contain config_global and zones_config objects")

    global_config = _global_config_from_dict(config_global, secrets_path)
    circuits = _circuits_from_zones_dict(zones_config, strict=True)
    return global_config, circuits


def _global_config_from_dict(data: dict[str, Any], secrets_path: str) -> GlobalConfig:
    """Validates and builds GlobalConfig from dictionary data."""

    _is_valid_global_config(data)  # if invalid, raises ValueError
    api_enabled = True
    
    data["weather_api"] = {
        "api_enabled": api_enabled,
        "realtime_url": data["weather_api"].get("realtime_url"),
        "history_url": data["weather_api"].get("history_url"),
        "api_key": data["weather_api"].get("api_key", ""),
        "application_key": data["weather_api"].get("application_key", ""),
        "device_mac": data["weather_api"].get("device_mac", "")
    }

    return GlobalConfig.from_dict(data)


def load_zones_config(filepath: str) -> list[IrrigationCircuit]:
    """
    Loads circuits configurations from JSON file and creates IrrigationCircuit objects for each circuit.
    """
    try:
        with open(filepath, "r") as f:
            config_data = json.load(f)
    except FileNotFoundError:
        # Log a warning and return an empty list if zones config file is not found, to allow runtime to start with no zones.
        logger.warning(f"Zones config file not found at path: {filepath}. No irrigation circuits will be loaded.")
        return []

    return _circuits_from_zones_dict(config_data, strict=False)


def _circuits_from_zones_dict(config_data: dict[str, Any], strict: bool) -> list[IrrigationCircuit]:
    """Builds IrrigationCircuit objects from zones config data."""
    zones = config_data.get("zones") if isinstance(config_data, dict) else None
    if not isinstance(zones, list):
        raise ValueError("zones_config must contain a 'zones' list")

    circuits = []
    for zone in zones:
        # Validate the zone configuration
        valid, errors = _is_valid_zone(zone)
        if not valid:
            zone_name = zone.get("name", "<unknown>") if isinstance(zone, dict) else "<unknown>"
            error_message = f"Invalid zone configuration for {zone_name}: {', '.join(errors)}"
            if strict:
                raise ValueError(error_message)
            # Legacy behavior: skip invalid zones while loading from file.
            logger.error(error_message)
            continue

        circuit = circuit_from_config(zone)
        circuits.append(circuit)

    return circuits


def circuit_from_config(zone: dict) -> IrrigationCircuit:
    """
    Creates IrrigationCircuit object from a JSON configuration dictionary (one zone-circuit).
    """
    name = zone["name"]
    number = zone["id"]
    relay_pin = zone["relay_pin"]
    enabled = zone["enabled"]

    even_area_mode = zone["even_area_mode"]
    if even_area_mode:
        target_mm = zone["target_mm"]
        zone_area_m2 = zone["zone_area_m2"]
        liters_per_minimum_dripper = None
    else:
        target_mm = None
        zone_area_m2 = None
        liters_per_minimum_dripper = zone["liters_per_minimum_dripper"]

    # Backwards-compatible: support both legacy `interval_days` and new `frequency_settings`
    frequency_settings = zone.get("frequency_settings", {}) if isinstance(zone, dict) else {}
    # Fallback to legacy single value
    interval_days = zone.get("interval_days") if isinstance(zone, dict) and zone.get("interval_days") is not None else int(frequency_settings.get("min_interval_days", 1))

    # not used in this version, but can be used for sensors
    # sensor_pins = zone.get("sensor_pins", [])  # expected to be a list of lists

    # Compute base_volume_liters and base_flow_lph from legacy fields (temporary)
    drippers_dict = zone.get("drippers_summary", {}) or {}
    total_consumption = 0.0
    min_dripper_flow = 0.0
    if isinstance(drippers_dict, dict) and drippers_dict:
        entries = [(int(k), int(v)) for k, v in drippers_dict.items()]
        total_consumption = float(sum(flow * count for flow, count in entries))  # liters per hour
        min_dripper_flow = float(min(flow for flow, _ in entries))

    # Determine base target volume
    if even_area_mode:
        base_volume_liters = target_mm * zone_area_m2
    else:
        # Fallback: compute duration using liters_per_minimum_dripper and min dripper flow
        if min_dripper_flow <= 0:
            base_volume_liters = 0.0
        else:
            duration_hours = (liters_per_minimum_dripper or 0) / min_dripper_flow
            base_volume_liters = total_consumption * duration_hours


    # Set local correction factors
    file_correction_factors = zone.get("local_correction_factors", {})
    correction_factors = CorrectionFactors(
        solar=file_correction_factors.get("solar", 5.0),
        rain=file_correction_factors.get("rain", 0.0),
        temperature= file_correction_factors.get("temperature", 15.0)
    )

    # Create FrequencySettings object
    frequency_settings = FrequencySettings(
        dynamic_interval=frequency_settings.get("dynamic_interval", False),
        min_interval_days=frequency_settings.get("min_interval_days", 1),
        max_interval_days=frequency_settings.get("max_interval_days", 5),
        carry_over_volume=frequency_settings.get("carry_over_volume", True),
        irrigation_volume_threshold_percent=frequency_settings.get("irrigation_volume_threshold_percent", 50),
    )

    zone_config = ZoneConfig(
        id=number,
        name=name,
        relay_pin=relay_pin,
        enabled=enabled,
        even_area_mode=even_area_mode,
        base_volume_liters=round(float(base_volume_liters or 0.0), 3),
        base_flow_lph=round(float(total_consumption or 0.0), 3),
        interval_days=interval_days,
        frequency_settings=frequency_settings,
        local_correction_factors=correction_factors
    )

    circuit = IrrigationCircuit(
        zone_config=zone_config,
    )

    return circuit


def _is_valid_zone(zone: dict) -> Tuple[bool, List[str]]:
    """
    Validates the structure of a zone configuration dictionary.
    """
    errors = []
    required_keys = [
        "name", "id", "relay_pin", "enabled", "even_area_mode",
        "target_mm", "zone_area_m2", "liters_per_minimum_dripper",
        "interval_days", "drippers_summary",
        "local_correction_factors"
    ]
    # REQUIRED_KEYS_COMMON = [...]
    # REQUIRED_KEYS_EVEN = [...]
    # REQUIRED_KEYS_DRIPPER = [...]

    # Check if all required keys are present
    for key in required_keys:
        if key not in zone:
            errors.append(f"Missing required key: {key}")

    # Check if even_area_mode == true - then target_mm and zone_area_m2 must be present and liters_per_minimum_dripper must be None
    # Otherwise, the liters_per_minimum_dripper must be present and target_mm and zone_area_m2 must be None
    if zone.get("even_area_mode", False):
        if zone.get("target_mm", None) is None or zone.get("zone_area_m2", None) is None or zone.get("liters_per_minimum_dripper") is not None:
            errors.append("Even area mode is True, but target_mm or zone_area_m2 is None or liters_per_minimum_dripper is present")
    else:
        if zone.get("target_mm") is not None or zone.get("zone_area_m2") is not None or zone.get("liters_per_minimum_dripper", None) is None:
            errors.append("Even area mode is False, but target_mm or zone_area_m2 is present or liters_per_minimum_dripper is None")

    # Check if drippers_summary is a dictionary with integer keys and values
    if not isinstance(zone.get("drippers_summary", None), dict):
        errors.append("drippers_summary must be a dictionary")
    else:
        for flow_rate_str, count in zone["drippers_summary"].items():
            if not flow_rate_str.isdigit() or not isinstance(count, int):
                errors.append(f"Invalid dripper summary entry: {flow_rate_str}: {count}")
    
    # Check if local_correction_factors is a dictionary with valid keys
    local_cf = zone.get("local_correction_factors", {})
    if not isinstance(local_cf, dict):
        errors.append("local_correction_factors must be a dictionary")
    else:
        for key in ["solar", "rain", "temperature"]:
            if key in local_cf and not isinstance(local_cf[key], (float, int)):
                errors.append(f"local_correction_factors.{key} must be a number")
    
    return len(errors) == 0, errors


def _is_valid_global_config(data: dict):
    """
    Validates the structure and types in the global config dictionary.
    Raises ValueError if something is invalid.
    """
    required_sections = [
        "standard_conditions",
        "correction_factors",
        "irrigation_limits",
        "automation",
        "logging",
        "weather_api"
    ]
    for section in required_sections:
        if section not in data:
            raise ValueError(f"Missing section: {section}")

    # Validate standard_conditions
    sc = data["standard_conditions"]
    if not isinstance(sc.get("solar_total"), (float, int)):
        raise ValueError("standard_conditions.solar_total must be a number")
    if not isinstance(sc.get("rain_mm"), (float, int)):
        raise ValueError("standard_conditions.rain_mm must be a number")
    if not isinstance(sc.get("temperature_celsius"), (float, int)):
        raise ValueError("standard_conditions.temperature_celsius must be a number")

    # Validate correction_factors
    cf = data["correction_factors"]
    for key in ["solar", "rain", "temperature"]:
        if not isinstance(cf.get(key), (float, int)):
            raise ValueError(f"correction_factors.{key} must be a number")

    # Validate irrigation_limits
    il = data["irrigation_limits"]
    if not isinstance(il.get("min_percent"), int):
        raise ValueError("irrigation_limits.min_percent must be an int")
    if not isinstance(il.get("max_percent"), int):
        raise ValueError("irrigation_limits.max_percent must be an int")
    if not isinstance(il.get("main_valve_max_flow"), (float, int, type(None))):
        raise ValueError("irrigation_limits.main_valve_max_flow must be a number")

    # Validate automation
    auto = data["automation"]
    if not isinstance(auto.get("enabled"), bool):
        raise ValueError("automation.enabled must be a boolean")
    if not isinstance(auto.get("sequential"), bool):
        raise ValueError("automation.sequential must be a boolean")
    if not isinstance(auto.get("scheduled_hour"), int):
        raise ValueError("automation.scheduled_hour must be an int")
    if not isinstance(auto.get("scheduled_minute"), int):
        raise ValueError("automation.scheduled_minute must be an int")
    if not isinstance(auto.get("max_flow_monitoring"), bool):
        raise ValueError("automation.max_flow_monitoring must be a boolean")
    if not isinstance(auto.get("environment"), str):
        raise ValueError("automation.environment must be a string")
    if not isinstance(auto.get("environment"), str):
        raise ValueError("automation.environment must be a string")
    if not isinstance(auto.get("use_weathersimulator"), bool):
        raise ValueError("automation.use_weathersimulator must be a boolean")

    # Validate logging
    log = data["logging"]
    if not isinstance(log.get("enabled"), bool):
        raise ValueError("logging.enabled must be a boolean")
    if log.get("log_level") not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError("logging.log_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    
    # Validate weather_api
    weather_api = data.get("weather_api", {})
    if not isinstance(weather_api.get("realtime_url"), str):
        raise ValueError("weather_api.realtime_url must be a string")
    if not isinstance(weather_api.get("history_url"), str):
        raise ValueError("weather_api.history_url must be a string")


# maybe useless, unused for now
def circuits_to_config(circuits: list) -> dict:
    """
    Returns a JSON-compatible dictionary representation of a list of IrrigationCircuit objects.
    """
    return {
        "zones": [circuit_to_config(c) for c in circuits]
    }


# maybe useless
def circuit_to_config(circuit: IrrigationCircuit) -> dict:
    """
    Returns a JSON-compatible dictionary representation of an IrrigationCircuit object.
    """
    return {
        "id": circuit.zone_config.id,
        "name": circuit.zone_config.name,
        "relay_pin": circuit.zone_config.relay_pin,
        "enabled": circuit.zone_config.enabled,
        "even_area_mode": circuit.zone_config.even_area_mode,
        "base_volume_liters": circuit.zone_config.base_volume_liters,
        "base_flow_lph": circuit.zone_config.base_flow_lph,
        "interval_days": circuit.zone_config.interval_days,
        "local_correction_factors": {"solar": circuit.zone_config.local_correction_factors.solar,
                                     "rain": circuit.zone_config.local_correction_factors.rain,
                                     "temperature": circuit.zone_config.local_correction_factors.temperature},
        "frequency_settings": {
            "dynamic_interval": circuit.zone_config.frequency_settings.dynamic_interval,
            "min_interval_days": circuit.zone_config.frequency_settings.min_interval_days,
            "max_interval_days": circuit.zone_config.frequency_settings.max_interval_days,
            "carry_over_volume": circuit.zone_config.frequency_settings.carry_over_volume,
            "irrigation_volume_threshold_percent": circuit.zone_config.frequency_settings.irrigation_volume_threshold_percent},
    }