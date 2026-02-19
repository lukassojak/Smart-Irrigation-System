from datetime import datetime, timezone

from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.models.zone import Zone


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
        "relay_pin": zone.relay_pin,
        "enabled": zone.enabled,
        "irrigation_mode": zone.irrigation_mode.value,
        "local_correction_factors": zone.local_correction_factors,
        "frequency_settings": zone.frequency_settings,
        "fallback_strategy": zone.fallback_strategy,
        "irrigation_configuration": zone.irrigation_configuration,
        "emitters_configuration": zone.emitters_configuration,
    }
    return zone_config