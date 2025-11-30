# smart_irrigation_system/node/core/controller/status_aggregator.py

from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit

from smart_irrigation_system.node.core.status_models import CircuitSnapshot, CircuitRuntimeStatus, CircuitStatus


class StatusAggregator:
    """
    Combines runtime and persistent snapshots into a unified status view for each irrigation circuit.
    """

    def __init__(self, circuits: dict[int, IrrigationCircuit],
                 state_manager: CircuitStateManager):
        self.circuits = circuits
        self.state_manager = state_manager

    def get_circuit_status(self, circuit_id: int) -> CircuitStatus:
        """
        Get the combined status for a specific circuit.
        
        :param circuit_id: ID of the circuit to get status for.
        :return: CircuitStatus object combining runtime and snapshot data.
        :raises ValueError: if the circuit_id is not found.
        """
        try:
            circuit = self.circuits[circuit_id]
        except KeyError:
            raise ValueError(f"Circuit ID {circuit_id} not found in circuits.")
        runtime_status: CircuitRuntimeStatus = circuit.runtime_status
        snapshot: CircuitSnapshot = self.state_manager.get_circuit_snapshot(circuit_id)
        return CircuitStatus(
            circuit_id=circuit_id,
            name=circuit.name,
            runtime_status=runtime_status,
            snapshot=snapshot
        )

    def get_all_statuses(self) -> dict[int, CircuitStatus]:
        """
        Get the combined status for all circuits.
        
        :return: Dictionary mapping circuit IDs to their CircuitStatus objects.
        :raises ValueError: if any circuit_id is not found.
        """
        statuses = {}
        for circuit_id in self.circuits.keys():
            statuses[circuit_id] = self.get_circuit_status(circuit_id)
        return statuses