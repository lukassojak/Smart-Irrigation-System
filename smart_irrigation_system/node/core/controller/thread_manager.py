# smart_irrigation_system/node/core/controller/thread_manager.py

import threading
import time

from collections.abc import Callable
from enum import Enum

from smart_irrigation_system.node.utils.logger import get_logger
from smart_irrigation_system.node.utils.time_utils import deadline_from_now, remaining_time

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

        The provided timeout is a total deadline for the whole operation, not a per-worker timeout.
        Each worker is joined in rounds with the remaining time budget so one stuck worker does not
        prevent the rest of the workers from being attempted to join.

        :param task_type: if specified, only join workers of this type.
        :param timeout: maximum total time to wait for the whole join operation. Defaults to 10 seconds.
        :raises TimeoutError: if any worker still remains alive after the deadline.
        """

        self.logger.debug(f"Joining all workers of type '{task_type or 'any'}' with total timeout {timeout} seconds.")
        with self._lock:
            workers_to_join = [
                worker_handle for worker_handle in self._workers.values()
                if task_type is None or worker_handle.task_type == task_type
            ]

        deadline = deadline_from_now(timeout)
        remaining_workers = list(workers_to_join)

        while remaining_workers:
            if remaining_time(deadline) <= 0:
                break

            next_remaining_workers = []
            for worker_handle in remaining_workers:
                wait_time = remaining_time(deadline)
                if wait_time <= 0:
                    next_remaining_workers.append(worker_handle)
                    continue

                worker_handle.thread.join(timeout=wait_time)
                self.logger.debug(
                    f"Join returned for worker '{worker_handle.name}', "
                    f"is_alive={worker_handle.thread.is_alive()}"
                )
                if worker_handle.thread.is_alive():
                    next_remaining_workers.append(worker_handle)

            remaining_workers = next_remaining_workers

        if remaining_workers:
            names = ", ".join(worker_handle.name for worker_handle in remaining_workers)
            raise TimeoutError(
                f"Workers failed to join within {timeout} seconds: {names}"
            )

    
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