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


def circuit_from_config(zone: dict) -> IrrigationCircuit:
    """
    Creates IrrigationCircuit object from a JSON configuration dictionary (one zone-circuit).
    """
    name = zone["name"]
    number = zone["id"]
    relay_pin = zone["relay_pin"]
    enabled = zone["enabled"]
    standard_flow_seconds = zone["standard_flow_seconds"]
    interval_days = zone["interval_days"]

    # not used in this version, but can be used for sensors
    # sensor_pins = zone.get("sensor_pins", [])  # expected to be a list of lists

    drippers = Drippers()
    # Add drippers to the drippers instance
    drippers_list = zone.get("drippers", [])
    for dripper in drippers_list:
        lph = dripper["liters_per_hour"]
        drippers.add_dripper(lph)
    
    # Set local correction factors
    correction_factors = CorrectionFactors(
        sunlight=zone.get("sunlight"),
        rain=zone.get("rain"),
        temperature=zone.get("temperature")
    )

    # Create the IrrigationCircuit object
    circuit = IrrigationCircuit(
        name=name,
        circuit_number=number,
        relay_pin=relay_pin,
        enabled=enabled,
        standard_flow_seconds=standard_flow_seconds,
        interval_days=interval_days,
        drippers=drippers,
        correction_factors=correction_factors
    )

    return circuit


# maybe useless
def circuits_to_config(circuits: list) -> dict:
    """
    Převod všech IrrigationCircuit objektů zpět do struktury JSON pro uložení.
    """
    return {
        "zones": [circuit_to_config(c) for c in circuits]
    }


# maybe useless
def circuit_to_config(circuit: IrrigationCircuit) -> dict:
    """
    Převod jednoho IrrigationCircuit objektu zpět do JSON záznamu.
    """
    return {
        "id": circuit.number,
        "name": circuit.name,
        "relay_pin": circuit.valve.relay_pin,
        "sensor_pins": [[s.pin1, s.pin2] for s in circuit.sensors],
        "drippers": [{"liters_per_hour": d.liters_per_hour} for d in circuit.drippers],
        "interval_days": getattr(circuit, "interval_days", 1),
        "watering_multiplier": getattr(circuit, "watering_multiplier", 1.0),
        "max_daily_volume_liters": getattr(circuit, "max_daily_volume_liters", 10.0)
    }