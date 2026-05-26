import threading

from smart_irrigation_system.node.core.controller.irrigation_executor import IrrigationExecutor, RunningCircuitTask
from smart_irrigation_system.node.core.controller.thread_manager import WorkerHandle, TaskType


class FakeThreadManager:
    def __init__(self):
        self.join_called_with = None
        self.join_timeout = None

    def join_worker_handle(self, worker_handle: WorkerHandle, timeout: float = 10.0) -> None:
        self.join_called_with = worker_handle
        self.join_timeout = timeout


def test_stop_circuit_irrigation_sets_local_event_and_joins_worker():
    thread_manager = FakeThreadManager()
    executor = IrrigationExecutor(
        circuits={},
        state_manager=object(),
        thread_manager=thread_manager,
    )

    callbacks = []
    executor.register_callbacks(
        on_irrigation_stop_requested=lambda: callbacks.append("stop_requested"),
        on_irrigation_stopped=lambda: callbacks.append("stopped"),
    )

    local_stop_event = threading.Event()
    worker_handle = WorkerHandle(
        thread=threading.Thread(target=lambda: None),
        name="irrigation-12",
        task_type=TaskType.IRRIGATION,
    )

    executor._running_tasks[12] = RunningCircuitTask(
        circuit_id=12,
        worker_handle=worker_handle,
        stop_event=local_stop_event,
    )

    executor.stop_circuit_irrigation(circuit_id=12, timeout=3.0)

    assert local_stop_event.is_set()
    assert thread_manager.join_called_with is worker_handle
    assert thread_manager.join_timeout == 3.0
    assert callbacks == ["stop_requested", "stopped"]


def test_stop_circuit_irrigation_is_noop_when_circuit_is_not_running():
    thread_manager = FakeThreadManager()
    executor = IrrigationExecutor(
        circuits={},
        state_manager=object(),
        thread_manager=thread_manager,
    )

    # Should not raise and should not call join when there is no running task.
    executor.stop_circuit_irrigation(circuit_id=999, timeout=1.0)

    assert thread_manager.join_called_with is None
