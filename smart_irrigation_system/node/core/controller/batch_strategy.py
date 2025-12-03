# smart_irrigation_system/node/core/controller/batch_strategy.py

# Not reactive to run-time changes during irrigation.
# Create interface for different batching strategies.

from smart_irrigation_system.node.interfaces import BatchStrategyLike, CircuitPlanningLike

class SimpleBatchStrategy(BatchStrategyLike):
    """
    Simplest possible version: returns one batch containing all circuits.
    Future strategies will implement staggering, max-flow monitoring, etc.
    """

    def select_batches(self, circuits: list[CircuitPlanningLike]) -> list[list[int]]:
        """Select all circuit ids in a single batch."""
        return [[c.id for c in circuits]]
