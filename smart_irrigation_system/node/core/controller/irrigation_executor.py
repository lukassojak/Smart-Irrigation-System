# smart_irrigation_system/node/core/controller/irrigation_executor.py

import threading
from collections.abc import Callable

from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.controller.task_planner import TaskPlanner
from smart_irrigation_system.node.core.controller.thread_manager import ThreadManager, TaskType, WorkerHandle


class IrrigationExecutor:
    def __init__(self,
                 circuits: dict[int, IrrigationCircuit],
                 state_manager: CircuitStateManager,
                 thread_manager: ThreadManager,
                 on_circuit_done: Callable[[int], None] | None = None):
        self.circuits = circuits
        self.state_manager = state_manager
        self.thread_manager = thread_manager
        self.on_circuit_done = on_circuit_done

        self.stop_event = threading.Event()

    def execute_plan(self, planner: TaskPlanner, global_config: GlobalConfig, conditions_provider) -> None:
        """
        Execute the irrigation plan prepared by the TaskPlanner.
        
        :param planner: TaskPlanner with prepared plan. Must be already planned by calling planner.plan().
        :param global_config: Global configuration of the node.
        :param conditions_provider: Provider of current weather conditions.
        """
        while True:
            batch = planner.get_next_batch()
            if batch is None:
                break

            # Start irrigation for each circuit in the batch
            for circuit_id in batch:
                self._start_irrigation(circuit_id, planner, global_config, conditions_provider)
            
            # Wait for all circuits in the batch to complete
            # Includes also all manually started irrigation tasks
            self.thread_manager.join_all_workers(task_type=TaskType.IRRIGATION)


    def stop_all_irrigation(self, timeout: float = 10.0) -> None:
        """
        Signal all irrigation tasks to stop. Wait for their termination.

        :param timeout: Maximum time to wait for all irrigation tasks to stop.
        :raises TimeoutError: if not all tasks stop within the timeout.
        """

        self.stop_event.set()
        self.thread_manager.join_all_workers(task_type=TaskType.IRRIGATION, timeout=timeout)


    def _start_irrigation(self, circuit_id: int, planner: TaskPlanner,
                          global_config: GlobalConfig, conditions_provider) -> None:
        def worker():
            try:
                self.state_manager.irrigation_started(circuit_id)
                result: IrrigationResult = circuit.irrigate_auto(
                    global_config=global_config,
                    conditions_provider=conditions_provider,
                    stop_event=self.stop_event
                )
                self.state_manager.irrigation_finished(circuit_id, result)
            # TODO: replace with specific exceptions
            except Exception as e:
                # TODO: implement irrigation failure handling in CircuitStateManager
                self.state_manager.irrigation_failed(circuit_id, str(e))
            finally:
                planner.mark_done(circuit_id)
                if self.on_circuit_done:
                    self.on_circuit_done(circuit_id)

        circuit = self.circuits[circuit_id]
        planner.mark_running(circuit_id)
        self.thread_manager.start_irrigation_worker(circuit_id, worker)