# smart_irrigation_system/node/core/controller/task_scheduler.py

import threading

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

import smart_irrigation_system.node.utils.time_utils as time_utils

from smart_irrigation_system.node.core.controller.thread_manager import ThreadManager, TaskType, WorkerHandle

from smart_irrigation_system.node.utils.logger import get_logger


LOOP_SLEEP_INTERVAL = 1.0  # seconds


@dataclass
class ScheduledTask:
    name: str
    fn: Callable
    interval: int  # seconds
    async_mode: bool
    last_run: datetime | None = None
    initial_delay: float = 0.0  # seconds


class TaskScheduler:
    """Cron-like scheduler for node periodic background tasks."""

    def __init__(self, thread_manager: ThreadManager):
        self.thread_manager = thread_manager
        self.tasks: dict[str, ScheduledTask] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self.logger = get_logger(self.__class__.__name__)


    def register_task(self, name: str, fn: Callable,
                      interval: int, async_mode: bool = True,
                      initial_delay: float = 0.0) -> None:
        """
        Register a periodic task.

        :param name: Unique name of the task.
        :param fn: Function to execute periodically.
        :param interval: Interval between executions in seconds.
        :param async_mode: If True, the task runs in a separate thread.
        :param initial_delay: Initial delay before the first execution in seconds.
        :raises ValueError: if a task with the same name is already registered.
        """

        if name in self.tasks:
            raise ValueError(f"Task with name '{name}' is already registered.")
        
        self.tasks[name] = ScheduledTask(
            name=name,
            fn=fn,
            interval=interval,
            async_mode=async_mode,
            initial_delay=initial_delay
        )

        self.logger.info(f"Registered task '{name}' with interval {interval}s (async_mode={async_mode}, initial_delay={initial_delay}s).")


    def unregister_task(self, name: str) -> None:
        """
        Unregister a periodic task.

        :param name: Name of the task to unregister.
        :raises ValueError: if a task with the given name is not registered.
        """

        if name not in self.tasks:
            raise ValueError(f"Task with name '{name}' is not registered.")
        self.tasks.pop(name)

        self.logger.info(f"Unregistered task '{name}'.")


    def start(self) -> None:
        """Start the task scheduler."""

        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="TaskScheduler", daemon=True)
        self._thread.start()
        self.logger.info("TaskScheduler started.")
    

    def stop(self, timeout: float = 10.0) -> None:
        """
        Stop the task scheduler. Wait for the scheduler thread to terminate.

        :param timeout: maximum time to wait for the scheduler thread to stop. Defaults to 10 seconds.
        :raises TimeoutError: if the scheduler thread fails to stop within the given timeout.
        """

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                raise TimeoutError("Failed to stop TaskScheduler thread within the given timeout.")
            self._thread = None
        
        self.logger.info("TaskScheduler stopped.")


    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            now = time_utils.now()
            for task in self.tasks.values():
                if task.last_run is None:
                    if task.initial_delay > 0:
                        # Not yet time for the first run
                        if time_utils.elapsed_seconds(now - timedelta(seconds=task.initial_delay), now) < 0:
                            continue
                    # First run
                    self._execute_task(task)
                else:
                    elapsed = time_utils.elapsed_seconds(task.last_run, now)
                    if elapsed >= task.interval:
                        self._execute_task(task)
            
            # Sleep a short while to avoid busy waiting
            self._stop_event.wait(timeout=LOOP_SLEEP_INTERVAL)
    

    def _execute_task(self, task: ScheduledTask) -> None:
        task.last_run = time_utils.now()
        if task.async_mode:
            self.thread_manager.start_general_worker(
                task_name=task.name,
                target_fn=task.fn
            )
        else:
            try:
                task.fn()
            except Exception as e:
                # Log or handle exception as needed, e.g., send to ControllerCore
                pass
            

    
