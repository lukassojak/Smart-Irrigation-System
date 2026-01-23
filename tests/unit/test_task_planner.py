import pytest

from smart_irrigation_system.node.core.controller.task_planner import TaskPlanner, PlannedTask, PlannedState

from smart_irrigation_system.node.interfaces import CircuitPlanningLike, BatchStrategyLike


# ---------------------- Fakes ----------------------

class FakeCircuitPlanning(CircuitPlanningLike):
    def __init__(self, circuit_id: int, needs: bool):
        self.id = circuit_id
        self._needs = needs

    def needs_irrigation(self, _) -> bool:
        return self._needs
    
class FakeBatchStrategy(BatchStrategyLike):
    def select_batches(self, circuits: list[CircuitPlanningLike]) -> list[list[int]]:
        return [[c.id for c in circuits]]

class FakeBatchStrategySequential(BatchStrategyLike):
    def select_batches(self, circuits: list[CircuitPlanningLike]) -> list[list[int]]:
        return [[c.id] for c in circuits]
    

# ---------------------- Fixtures ----------------------

@pytest.fixture
def planner() -> TaskPlanner:
    return TaskPlanner(FakeBatchStrategy())

@pytest.fixture
def planner_sequential_strategy() -> TaskPlanner:
    return TaskPlanner(FakeBatchStrategySequential())

@pytest.fixture
def state_manager():
    return object()

@pytest.fixture
def circuits_mixed() -> dict[int, CircuitPlanningLike]:
    return {
        1: FakeCircuitPlanning(1, True),
        2: FakeCircuitPlanning(2, True),
        3: FakeCircuitPlanning(3, False),
        4: FakeCircuitPlanning(4, True),
        5: FakeCircuitPlanning(5, False)
    }


# ---------------------- Tests ----------------------

def test_planner_has_no_batches_initially(planner):
    assert (planner.get_next_batch() is None) and (planner.batches == [])


def test_planner_creates_tasks_only_for_circuits_that_need_irrigation(planner, state_manager, circuits_mixed):

    # Act
    planner.plan(circuits_mixed, state_manager)

    # Assert
    assert set(planner.tasks.keys()) == {1, 2, 4}
    for task in planner.tasks.values():
        assert isinstance(task, PlannedTask)


def test_planner_uses_batch_strategy(planner, state_manager):
    # Arrange
    circuits = {
        1: FakeCircuitPlanning(1, True),
        2: FakeCircuitPlanning(2, True),
        3: FakeCircuitPlanning(3, True),
        4: FakeCircuitPlanning(4, True)
    }

    # Act
    planner.plan(circuits, state_manager)

    # Assert
    assert planner.batches == [[1, 2, 3, 4]]
    assert planner.get_next_batch() == [1, 2, 3, 4]
    assert planner.get_next_batch() == None


def test_planner_uses_batch_strategy_sequential(planner_sequential_strategy, state_manager):
    # Arrange
    circuits = {
        1: FakeCircuitPlanning(1, True),
        2: FakeCircuitPlanning(2, True),
        3: FakeCircuitPlanning(3, True),
        4: FakeCircuitPlanning(4, True)
    }

    # Act
    planner_sequential_strategy.plan(circuits, state_manager)

    # Assert
    assert planner_sequential_strategy.batches == [[1], [2], [3], [4]]
    assert planner_sequential_strategy.get_next_batch() == [1]
    assert planner_sequential_strategy.get_next_batch() == [2]
    assert planner_sequential_strategy.get_next_batch() == [3]
    assert planner_sequential_strategy.get_next_batch() == [4]
    assert planner_sequential_strategy.get_next_batch() == None


def test_tasks_remain_pending_before_running_or_done(planner, state_manager, circuits_mixed):
    # Arrange
    planner.plan(circuits_mixed, state_manager)
    planner.get_next_batch()

    # Assert
    assert planner.tasks[1].state == PlannedState.PENDING
    assert planner.tasks[4].state == PlannedState.PENDING


def test_mark_running_and_done_changes_state(planner, state_manager):
    # Arrange
    circuits = {
        1: FakeCircuitPlanning(1, True),
        2: FakeCircuitPlanning(2, True),
        3: FakeCircuitPlanning(3, False),
        4: FakeCircuitPlanning(4, True),
        5: FakeCircuitPlanning(5, False)
    }
    planner.plan(circuits, state_manager)
    planner.get_next_batch()

    # Act & assert
    planner.mark_running(1)
    planner.mark_running(4)

    assert planner.tasks[1].state == PlannedState.RUNNING
    assert planner.tasks[4].state == PlannedState.RUNNING

    planner.mark_done(1)
    planner.mark_done(4)

    assert planner.tasks[1].state == PlannedState.DONE
    assert planner.tasks[4].state == PlannedState.DONE


def test_mark_on_invalid_id_raises_exception(planner, state_manager, circuits_mixed):
    # Arrange
    planner.plan(circuits_mixed, state_manager)
    planner.get_next_batch()

    # Assert
    with pytest.raises(KeyError):
        planner.mark_running(999)
    
    with pytest.raises(KeyError):
        planner.mark_done(999)