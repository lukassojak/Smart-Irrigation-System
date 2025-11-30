# smart_irrigation_system/node/core/controller/batch_strategy.py

# Not reactive to run-time changes during irrigation.
# Create interface for different batching strategies.

class BatchStrategy:
    """
    Simplest possible version: returns one batch containing all circuits.
    Future strategies will implement staggering, max-flow monitoring, etc.
    """

    def select_batches(self, circuit_ids: list[int]) -> list[list[int]]:
        """Select all circuits in a single batch."""
        return [circuit_ids]
