import json
from smart_irrigation_system.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.drippers import Drippers
from smart_irrigation_system.correction_factors import CorrectionFactors
from smart_irrigation_system.global_config import GlobalConfig
from smart_irrigation_system.logger import get_logger
from smart_irrigation_system.secrets import get_secret
from typing import Tuple, List

# Initialize logger
logger = get_logger("config_loader")


def load_global_config(filepath: str) -> GlobalConfig:
    with open(filepath, "r") as f:
        data = json.load(f)

    _is_valid_global_config(data)       # if invalid, raises ValueError
    try:
        api_key, application_key, device_mac = get_secret("api_key"), get_secret("application_key"), get_secret("device_mac")
        api_enabled = True
    except Exception as e:
        if data.get("automation").get("environment") == "production":
            logger.error("Weather API keys are required in production environment.")
            logger.info("Empty file 'config_secrets.json' created, please fill it with your API keys.")
            raise ValueError("Weather API keys are required in production environment") from e
        else:
            # In non-production environments, we can use dummy values
            logger.warning("Using dummy weather API keys in non-production environment.")
            api_key, application_key, device_mac = "dummy_api_key", "dummy_application_key", "00:00:00:00:00:00"
            api_enabled = False
    
    data["weather_api"] = {
        "api_enabled": api_enabled,
        "realtime_url": data["weather_api"].get("realtime_url"),
        "history_url": data["weather_api"].get("history_url"),
        "api_key": api_key,
        "application_key": application_key,
        "device_mac": device_mac
    }

    return GlobalConfig.from_dict(data)


def load_zones_config(filepath: str) -> list[IrrigationCircuit]:
    """
    Loads circuits configurations from JSON file and creates IrrigationCircuit objects for each circuit.
    """
    with open(filepath, "r") as f:
        config_data = json.load(f)

    circuits = []
    for zone in config_data["zones"]:
        # Validate the zone configuration
        valid, errors = _is_valid_zone(zone)
        if not valid:
            # log the error and skip the invalid zone
            print(f"Invalid zone configuration for {zone['name']}: {', '.join(errors)}")
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

    interval_days = zone["interval_days"]

    # not used in this version, but can be used for sensors
    # sensor_pins = zone.get("sensor_pins", [])  # expected to be a list of lists

    drippers = Drippers()
    # Add drippers to the drippers instance
    drippers_dict = zone.get("drippers_summary", {})
    for dripper_flow_str, count in drippers_dict.items():
        for _ in range(count):
            drippers.add_dripper(int(dripper_flow_str))
        

    # Set local correction factors
    file_correction_factors = zone.get("local_correction_factors", {})
    correction_factors = CorrectionFactors(
        sunlight=file_correction_factors.get("sunlight", 55.0),
        rain=file_correction_factors.get("rain", 55.0),
        temperature= file_correction_factors.get("temperature", 55.0)
    )

    # Create the IrrigationCircuit object
    circuit = IrrigationCircuit(
        name=name,
        circuit_id=number,
        relay_pin=relay_pin,
        enabled=enabled,
        even_area_mode=even_area_mode,
        target_mm=target_mm,
        zone_area_m2=zone_area_m2,
        liters_per_minimum_dripper=liters_per_minimum_dripper,
        interval_days=interval_days,
        drippers=drippers,
        correction_factors=correction_factors
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
        for key in ["sunlight", "rain", "temperature"]:
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
    if not isinstance(sc.get("sunlight_hours"), (float, int)):
        raise ValueError("standard_conditions.sunlight_hours must be a number")
    if not isinstance(sc.get("rain_mm"), (float, int)):
        raise ValueError("standard_conditions.rain_mm must be a number")
    if not isinstance(sc.get("temperature_celsius"), (float, int)):
        raise ValueError("standard_conditions.temperature_celsius must be a number")

    # Validate correction_factors
    cf = data["correction_factors"]
    for key in ["sunlight", "rain", "temperature"]:
        if not isinstance(cf.get(key), (float, int)):
            raise ValueError(f"correction_factors.{key} must be a number")

    # Validate irrigation_limits
    il = data["irrigation_limits"]
    if not isinstance(il.get("min_percent"), int):
        raise ValueError("irrigation_limits.min_percent must be an int")
    if not isinstance(il.get("max_percent"), int):
        raise ValueError("irrigation_limits.max_percent must be an int")
    if not isinstance(il.get("main_valve_max_flow"), (float, int)):
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


# maybe useless
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
        "id": circuit.id,
        "name": circuit.name,
        "relay_pin": circuit.valve.relay_pin,
        "enabled": circuit.enabled,
        "even_area_mode": circuit.even_area_mode,
        "target_mm": circuit.target_mm,
        "zone_area_m2": circuit.zone_area_m2,
        "liters_per_minimum_dripper": circuit.liters_per_minimum_dripper,
        "interval_days": circuit.interval_days,
        "drippers_summary": {str(flow_rate): count for flow_rate, count in circuit.drippers.drippers.items()},
        "local_correction_factors": {"sunlight": circuit.correction_factors.get_factor("sunlight"),
                                     "rain": circuit.correction_factors.get_factor("rain"),
                                     "temperature": circuit.correction_factors.get_factor("temperature")},
    }