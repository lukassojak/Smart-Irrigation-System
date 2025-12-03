# smart_irrigation_system/node/core/controller/task_planner.py

from enum import Enum, auto

from smart_irrigation_system.node.interfaces import BatchStrategyLike, CircuitPlanningLike

from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager

class PlannedState(Enum):
    PENDING = auto()
    READY = auto()
    RUNNING = auto()
    DONE = auto()


class PlannedTask:
    def __init__(self, circuit_id: int):
        self.circuit_id = circuit_id
        self.state = PlannedState.PENDING


class TaskPlanner:
    """
    Planner responsible for preparing execution plan (batches of circuits).
    Does not run irrigation – only planning.
    """
    
    def __init__(self, batch_strategy: BatchStrategyLike):
        self.batch_strategy: BatchStrategyLike = batch_strategy
        self.tasks: dict[int, PlannedTask] = {}
        self.batches: list[list[int]] = []
        self.batch_index: int = 0

    def plan(self,
             circuits: dict[int, CircuitPlanningLike],
             state_manager: CircuitStateManager) -> None:
        """Prepare planner internal state."""

        # Filter circuits that need irrigation
        filtered_circuits: dict[int, CircuitPlanningLike] = {
            circuit_id: circuit for circuit_id, circuit in circuits.items()
            if circuit.needs_irrigation(state_manager)
        }
        
        self.tasks: dict[int, PlannedTask] = {
            circuit_id: PlannedTask(circuit_id)
            for circuit_id, _ in filtered_circuits.items()
        }

        self.batches = self.batch_strategy.select_batches(list(filtered_circuits.values()))
        self.batch_index = 0
    
    def get_next_batch(self) -> list[int] | None:
        """Return the next batch of circuit IDs to run, or None if all batches are done."""
        if self.batch_index >= len(self.batches):
            return None
        batch = self.batches[self.batch_index]
        self.batch_index += 1
        return batch
    
    def mark_running(self, circuit_id: int):
        """
        Mark the task for the given circuit ID as RUNNING.
        :throws KeyError: if circuit_id is not found in tasks.
        """
        self.tasks[circuit_id].state = PlannedState.RUNNING
    
    def mark_done(self, circuit_id: int):
        """
        Mark the task for the given circuit ID as DONE.
        :throws KeyError: if circuit_id is not found in tasks.
        """
        self.tasks[circuit_id].state = PlannedState.DONE
