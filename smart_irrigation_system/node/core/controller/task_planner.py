# smart_irrigation_system/node/core/controller/task_planner.py

# TODO: Create interface for BatchStrategy and implement TaskPlanner using it.

from enum import Enum, auto

from smart_irrigation_system.node.core.controller.batch_strategy import BatchStrategy


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
    
    def __init__(self, batch_strategy):
        self.batch_strategy: BatchStrategy = batch_strategy
        self.tasks: dict[int, PlannedTask] = {}
        self.batches: list[list[int]] = []
        self.batch_index = 0

    def plan(self, circuit_ids: list[int]):
        """Prepare planner internal state."""
        self.tasks = {cid: PlannedTask(cid) for cid in circuit_ids}
        self.batches = self.batch_strategy.select_batches(circuit_ids)
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
