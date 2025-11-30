# smart_irrigation_system/node/core/controller/thread_manager.py

import threading
from collections.abc import Callable
from enum import Enum


class TaskType(Enum):
    GENERAL = "general"
    IRRIGATION = "irrigation"
    SCHEDULER = "scheduler"


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

        with self._lock:
            workers_to_join = [
                worker_handle for worker_handle in self._workers.values()
                if task_type is None or worker_handle.task_type == task_type
            ]
        for worker_handle in workers_to_join:
            worker_handle.thread.join(timeout=timeout)
            if worker_handle.thread.is_alive():
                raise TimeoutError(f"Worker '{worker_handle.name}' failed to join within {timeout} seconds.")


    # ===========================================================================================================
    # Public API - Worker Queries
    # ===========================================================================================================

    def get_running_workers(self, task_type: TaskType | None = None) -> list[WorkerHandle]:
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
            except Exception as e:
                if self._exception_callback:
                    # TODO: add stack trace to exception info
                    self._exception_callback(worker_name, e)
                else:
                    raise
            finally:
                with self._lock:
                    self._workers.pop(worker_name, None)

        with self._lock:
            if worker_name in self._workers:
                raise ValueError(f"Worker with name '{worker_name}' already exists.")

            t = threading.Thread(target=worker_wrapper, daemon=True)
            t.start()
            handle = WorkerHandle(thread=t, name=worker_name, task_type=task_type)
            self._workers[worker_name] = handle
            return handle