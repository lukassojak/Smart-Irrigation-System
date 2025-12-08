# smart_irrigation_system/node/core/controller/irrigation_executor.py

import threading
from collections.abc import Callable

from smart_irrigation_system.node.interfaces import CircuitExecutionLike

from smart_irrigation_system.node.config.global_config import GlobalConfig

from smart_irrigation_system.node.utils.logger import get_logger

from smart_irrigation_system.node.core.circuit_state_manager import CircuitStateManager
from smart_irrigation_system.node.core.irrigation_circuit import IrrigationCircuit
from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.controller.task_planner import TaskPlanner
from smart_irrigation_system.node.core.controller.thread_manager import ThreadManager, TaskType, WorkerHandle

from smart_irrigation_system.node.weather.recent_weather_fetcher import RecentWeatherFetcher
from smart_irrigation_system.node.weather.weather_simulator import WeatherSimulator
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions

# Temporary constant for maximum irrigation time per batch for join timeout
MAX_IRRIGATING_TIME_PER_BATCH_SECONDS = 2 * 60 * 60  # 2 hours

class IrrigationExecutor:
    def __init__(self,
                 circuits: dict[int, CircuitExecutionLike],
                 state_manager: CircuitStateManager,
                 thread_manager: ThreadManager):
        self.circuits = circuits
        self.state_manager = state_manager
        self.thread_manager = thread_manager

        self.logger = get_logger(self.__class__.__name__)
        self.stop_event = threading.Event()

        self.register_callbacks()   # Register default no-op callbacks

    # ==================================================================================================================
    # Public API
    # ==================================================================================================================
    
    def register_callbacks(self,
                           on_irrigation_start: Callable = lambda: None,
                           on_auto_irrigation_finish: Callable = lambda: None,
                           on_man_irrigation_finish: Callable[[int], None] = lambda circuit_id: None,
                           on_irrigation_stopped: Callable = lambda: None,
                           on_executor_error: Callable[[int, Exception], None] = lambda circuit_id, e: None,
                           on_irrigation_waiting: Callable[[int, str], None] = lambda circuit_id, msg: None,
                           on_irrigation_failed: Callable[[int, str], None] = lambda circuit_id, reason: None,
                           on_irrigation_stop_requested: Callable = lambda: None
                           ) -> None:
        """
        Register callback functions for various irrigation events.
        """

        self._on_irrigation_start = on_irrigation_start
        self._on_auto_irrigation_finish = on_auto_irrigation_finish
        self._on_man_irrigation_finish = on_man_irrigation_finish
        self._on_irrigation_stopped = on_irrigation_stopped
        self._on_executor_error = on_executor_error
        self._on_irrigation_waiting = on_irrigation_waiting
        self._on_irrigation_failed = on_irrigation_failed
        self._on_irrigation_stop_requested = on_irrigation_stop_requested
    

    def execute_manual(self, circuit_id: int, volume: float) -> None:
        # Blocking call to execute manual irrigation for the specified circuit and target volume.
        # NOTE: This method currently does not handle flow control for manual irrigation.

        if self.circuits.get(circuit_id) is None:
            error_msg = f"Circuit ID {circuit_id} not found in executor circuits."
            self.logger.error(f"{error_msg} Aborting manual irrigation.")
            self._on_irrigation_failed(circuit_id, error_msg)
            return
        
        if not self.circuits.get(circuit_id).is_safe_to_irrigate():
            error_msg = f"Circuit ID {circuit_id} is not safe to irrigate."
            self.logger.warning(f"{error_msg} Aborting manual irrigation.")
            self._on_irrigation_failed(circuit_id, error_msg)
            return

        if volume <= 0:
            error_msg = f"Invalid target volume {volume}L for Circuit ID {circuit_id}. Must be positive."
            self.logger.error(f"{error_msg} Aborting manual irrigation.")
            self._on_irrigation_failed(circuit_id, error_msg)
            return
        
        self.logger.info(f"Starting manual irrigation for Circuit ID {circuit_id} with target volume {volume}L.")
        try:
            handle = self._start_man_irrigation(circuit_id, volume)
            self._on_irrigation_start()
            self.thread_manager.join_worker_handle(worker_handle=handle, timeout=MAX_IRRIGATING_TIME_PER_BATCH_SECONDS)
            self._on_man_irrigation_finish(circuit_id)
        except TimeoutError as e:
            self.logger.error(f"Manual irrigation for Circuit ID {circuit_id} timed out: {e}")
            self._on_executor_error(circuit_id, e)
        except Exception as e:
            self.logger.error(f"Unexpected error during manual irrigation execution: {e}")
            self._on_executor_error(circuit_id, e)


    def execute_plan(self, planner: TaskPlanner, global_config: GlobalConfig, conditions_provider: RecentWeatherFetcher | WeatherSimulator) -> None:
        """
        Execute the irrigation plan prepared by the TaskPlanner.
        
        :param planner: TaskPlanner with prepared plan. Must be already planned by calling planner.plan().
        :param global_config: Global configuration of the node.
        :param conditions_provider: Provider of current weather conditions.
        """

        try:
            while True:
                batch = planner.get_next_batch()
                if batch is None:
                    break
                
                current_conditions: GlobalConditions = conditions_provider.get_current_conditions()
                # Start irrigation for each circuit in the batch
                for circuit_id in batch:
                    circuit = self.circuits.get(circuit_id)
                    if circuit is None:
                        self.logger.error(f"Circuit ID {circuit_id} not found in executor circuits. Skipping.")
                        planner.mark_done(circuit_id)
                        continue
                    
                    if not circuit.is_safe_to_irrigate():
                        self.logger.warning(f"Circuit ID {circuit_id} is not safe to irrigate. Skipping.")
                        planner.mark_done(circuit_id)
                        continue
        
                    self.logger.info(f"Starting irrigation for Circuit ID {circuit_id}.")
                    self._start_auto_irrigation(circuit_id, planner, global_config, current_conditions)
                    self._on_irrigation_start()
                
                # Wait for all circuits in the batch to complete
                # Includes also all manually started irrigation tasks
                self.thread_manager.join_all_workers(task_type=TaskType.IRRIGATION, timeout=MAX_IRRIGATING_TIME_PER_BATCH_SECONDS)

            # All batches completed successfully
            self._on_auto_irrigation_finish()

        except TimeoutError as e:
            self.logger.error(f"Irrigation execution timed out: {e}")
            self._on_executor_error(-1, e)
        except Exception as e:
            self.logger.error(f"Unexpected error during irrigation execution: {e}")
            self._on_executor_error(-1, e)


    def stop_all_irrigation(self, timeout: float = 10.0) -> None:
        """
        Signal all irrigation tasks to stop. Wait for their termination.

        :param timeout: Maximum time to wait for all irrigation tasks to stop.
        :raises TimeoutError: if not all tasks stop within the timeout.
        """

        self.stop_event.set()
        self._on_irrigation_stop_requested()
        try:
            self.thread_manager.join_all_workers(task_type=TaskType.IRRIGATION, timeout=timeout)
            self._on_irrigation_stopped()
        except TimeoutError as e:
            self._on_executor_error(-1, e)
            raise e
        except Exception as e:
            self._on_executor_error(-1, e)
            raise e
        finally:
            self.stop_event.clear()


    # ==================================================================================================================
    # Private methods
    # ==================================================================================================================

    def _start_auto_irrigation(self, circuit_id: int, planner: TaskPlanner,
                          global_config: GlobalConfig, current_conditions: GlobalConditions) -> None:
        def worker():
            try:
                self.state_manager.irrigation_started(circuit_id)
                result: IrrigationResult = circuit.irrigate_auto(
                    global_config=global_config,
                    global_conditions=current_conditions,
                    stop_event=self.stop_event
                )
                self.state_manager.irrigation_finished(circuit_id, result)
                self.logger.info(f"Irrigation for Circuit ID {circuit_id} finalized.")
            # TODO: replace with specific exceptions
            except Exception as e:
                self.logger.error(f"Irrigation for Circuit ID {circuit_id} failed: {e}")
                self._on_executor_error(circuit_id, e)
                # TODO: implement irrigation failure handling in CircuitStateManager
                # self.state_manager.irrigation_failed(circuit_id, str(e))
            finally:
                planner.mark_done(circuit_id)

        circuit = self.circuits[circuit_id]
        planner.mark_running(circuit_id)
        try:
            self.thread_manager.start_irrigation_worker(circuit_id, worker)
        except ValueError as e:
            self.logger.warning(f"Failed to start irrigation worker for Circuit ID {circuit_id}: {e}")
            planner.mark_done(circuit_id)
    
    def _start_man_irrigation(self, circuit_id: int, volume: float) -> WorkerHandle:
        """
        Start manual irrigation for the specified circuit and target volume.
        
        :param circuit_id: ID of the circuit to irrigate.
        :param volume: Target volume to irrigate in liters.
        :raises ValueError: if the irrigation worker cannot be started.
        """

        def worker():
            try:
                self.state_manager.irrigation_started(circuit_id)
                result: IrrigationResult = circuit.irrigate_man(target_volume=volume,
                                                                stop_event=self.stop_event
                )
                self.state_manager.irrigation_finished(circuit_id, result)
                self.logger.info(f"Manual irrigation for Circuit ID {circuit_id} completed successfully.")
            except Exception as e:
                self.logger.error(f"Manual irrigation for Circuit ID {circuit_id} failed: {e}")
                self._on_executor_error(circuit_id, e)

        circuit = self.circuits[circuit_id]
        handle: WorkerHandle = self.thread_manager.start_irrigation_worker(circuit_id, worker)
        return handle
