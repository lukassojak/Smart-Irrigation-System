# smart_irrigation_system/node/core/controller/thread_manager.py

import threading

from collections.abc import Callable
from enum import Enum

from smart_irrigation_system.node.utils.logger import get_logger

from smart_irrigation_system.node.exceptions import WorkerThreadError, WorkerThreadAlreadyExistsError


class TaskType(Enum):
    GENERAL = "general"
    IRRIGATION = "irrigation"
    SCHEDULER = "scheduler"
    EXECUTOR = "executor"


class WorkerHandle:
    """
    Handle representing a running worker thread.
    """
    def __init__(self, thread: threading.Thread, name: str, task_type: TaskType):
        self.thread = thread
        self.name = name            # Unique worker name
        self.task_type = task_type

    
    def is_alive(self) -> bool:
        return self.thread.is_alive()
    

class ThreadManager:
    """
    Generic node-level thread manager. Handles:
    - starting/joining workers
    - exception handling via callbacks
    - worker lifecycle management
    - clean shutdown of all workers

    The ThreadManager is not responsible for stopping individual tasks;
    each worker must handle its own stop conditions by checking stop events.
    """
    def __init__(self):
        self._workers: dict[str, WorkerHandle] = {}
        self._lock = threading.Lock()
        self._exception_callback: Callable | None = None
        self.logger = get_logger(self.__class__.__name__)


    # ===========================================================================================================
    # Public API - Exception Handling
    # ===========================================================================================================

    def set_exception_callback(self, fn: Callable[[str, Exception], None]) -> None:
        """
        Register callback called when any worker thread raises an unhandled exception.
        
        :param fn: Callback function with signature fn(worker_name: str, exception: Exception) -> None
        """

        self._exception_callback = fn


    # ===========================================================================================================
    # Public API - Start Workers
    # ===========================================================================================================

    def start_worker(self, worker_name: str, task_type: TaskType, target_fn: Callable) -> WorkerHandle:
        """
        Starts a generic worker thread.

        :raises ValueError: if a worker with the given name already exists.
        """

        if not worker_name.startswith(f"{task_type.value}-"):
            worker_name = f"{task_type.value}-{worker_name}"

        return self._start_worker(worker_name, task_type, target_fn)
    
    def start_irrigation_worker(self, circuit_id: int, target_fn: Callable) -> WorkerHandle:
        """
        Starts a worker for a specific irrigation circuit.

        :raises ValueError: if a worker for the given circuit_id already exists.
        """

        worker_name = f"irrigation-{circuit_id}"
        return self.start_worker(worker_name, TaskType.IRRIGATION, target_fn)
    
    def start_general_worker(self, task_name: str, target_fn: Callable) -> WorkerHandle:
        """
        Starts a general-purpose worker.

        :raises ValueError: if a worker with the given task_name already exists.
        """

        if not task_name.startswith("general-"):
            task_name = f"general-{task_name}"
        return self.start_worker(task_name, TaskType.GENERAL, target_fn)
    
    def start_scheduler_worker(self, target_fn: Callable) -> WorkerHandle:
        """
        Starts the task scheduler worker.

        :raises ValueError: if the scheduler worker already exists.
        """

        worker_name = "scheduler-main"
        if self.get_running_workers(task_type=TaskType.SCHEDULER):
            raise ValueError("Scheduler worker already exists.")
        return self.start_worker(worker_name, TaskType.SCHEDULER, target_fn)


    # ===========================================================================================================
    # Public API - Worker Shutdown
    # ===========================================================================================================

    def join_all_workers(self, task_type: TaskType | None = None, timeout: float = 10.0) -> None:
        """
        Join all running workers, optionally filtered by task type.

        :param task_type: if specified, only join workers of this type.
        :param timeout: maximum time to wait for each worker to join. Defaults to 10 seconds.
        :raises TimeoutError: if any worker fails to join within the given timeout.
        """

        self.logger.debug(f"Joining all workers of type '{task_type or 'any'}' with timeout {timeout} seconds.")
        with self._lock:
            workers_to_join = [
                worker_handle for worker_handle in self._workers.values()
                if task_type is None or worker_handle.task_type == task_type
            ]
        for worker_handle in workers_to_join:
            worker_handle.thread.join(timeout=timeout)
            if worker_handle.thread.is_alive():
                raise TimeoutError(f"Worker '{worker_handle.name}' failed to join within {timeout} seconds.")

        self.logger.debug(f"All workers of type '{task_type or 'any'}' have been joined.")
    
    def join_worker_handle(self, worker_handle: WorkerHandle, timeout: float = 10.0) -> None:
        """
        Join a specific worker by its handle.

        :param worker_handle: WorkerHandle of the worker to join.
        :param timeout: maximum time to wait for the worker to join. Defaults to 10 seconds.
        :raises TimeoutError: if the worker fails to join within the given timeout.
        """

        self.logger.debug(f"Joining worker '{worker_handle.name}' with timeout {timeout} seconds.")
        worker_handle.thread.join(timeout=timeout)
        if worker_handle.thread.is_alive():
            raise TimeoutError(f"Worker '{worker_handle.name}' failed to join within {timeout} seconds.")
        self.logger.debug(f"Worker '{worker_handle.name}' has been joined.")


    # ===========================================================================================================
    # Public API - Worker Queries
    # ===========================================================================================================

    def get_running_workers(self, task_type: TaskType | None = None) -> list[WorkerHandle]:
        """
        Get a list of currently running workers, optionally filtered by task type.
        
        :param task_type: if specified, only return workers of this type.
        :return: List of WorkerHandle objects representing running workers.
        """
        with self._lock:
            return [
                worker_handle for worker_handle in self._workers.values()
                if (task_type is None or worker_handle.task_type == task_type) and worker_handle.is_alive()
            ]


    # ===========================================================================================================
    # Private Methods
    # ===========================================================================================================

    def _start_worker(self, worker_name: str, task_type: TaskType, target_fn: Callable) -> WorkerHandle:
        """
        Internal method to start a worker thread with exception handling and lifecycle management.
        
        :raises ValueError: if a worker with the same name already exists.
        """
        def worker_wrapper():
            try:
                target_fn()
                self.logger.debug(f"Worker '{worker_name}' finalized.")
            except Exception as e:
                if self._exception_callback:
                    # TODO: add stack trace to exception info
                    self._exception_callback(worker_name, e)
                else:
                    self.logger.error(f"Worker '{worker_name}' raised an unhandled exception: {e}")
                    raise e
            finally:
                with self._lock:
                    self._workers.pop(worker_name, None)
                self.logger.debug(f"Worker '{worker_name}' has been cleaned up. Current workers: {list(self._workers.keys())}")

        with self._lock:
            self.logger.debug(f"Checking for existing worker '{worker_name}' before starting new worker. Current workers: {list(self._workers.keys())}")
            if worker_name in self._workers.keys():
                raise WorkerThreadAlreadyExistsError(f"Worker with name '{worker_name}' already exists.")
            self.logger.debug(f"No existing worker '{worker_name}' found. Starting new worker.")

            t = threading.Thread(target=worker_wrapper, daemon=True)
            t.start()
            handle = WorkerHandle(thread=t, name=worker_name, task_type=task_type)
            self._workers[worker_name] = handle
            return handle