import json
from irrigation_circuit import IrrigationCircuit
from enums import TEMP_WATERING_TIME
from drippers import Drippers
from correction_factors import CorrectionFactors

def load_zones_config(filepath: str) -> list[IrrigationCircuit]:
    """
    Loads circuits configurations from JSON file and creates IrrigationCircuit objects for each circuit.
    """
    with open(filepath, "r") as f:
        config_data = json.load(f)

    circuits = []
    for zone in config_data["zones"]:
        circuit = circuit_from_config(zone)
        circuits.append(circuit)

    return circuits

def _is_valid_zone(zone: dict) -> bool:
    """
    Validates the structure of a zone configuration dictionary.
    """
    required_keys = [
        "name", "id", "relay_pin", "enabled", "even_area_mode",
        "target_mm", "zone_area_m2", "liters_per_minimum_dripper",
        "standard_flow_seconds", "interval_days", "drippers_summary"
    ]

    # Check if all required keys are present
    if not all(key in zone for key in required_keys):
        return False

    # Check if even_area_mode == true - then target_mm and zone_area_m2 must be present and liters_per_minimum_dripper must be None
    # Otherwise, the liters_per_minimum_dripper must be present and target_mm and zone_area_m2 must be None
    if zone["even_area_mode"]:
        if zone["target_mm"] is None or zone["zone_area_m2"] is None or zone["liters_per_minimum_dripper"] is not None:
            return False
    else:
        if zone["target_mm"] is not None or zone["zone_area_m2"] is not None or zone["liters_per_minimum_dripper"] is None:
            return False
        
    return True

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

    standard_flow_seconds = zone["standard_flow_seconds"]
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
    correction_factors = CorrectionFactors(
        sunlight=zone.get("sunlight"),
        rain=zone.get("rain"),
        temperature=zone.get("temperature")
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