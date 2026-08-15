import time

from smart_irrigation_system.node.utils.logger import get_logger


DEFAULT_INTERVAL = 60


class ProcessHeartbeat:
    """Periodically writes a timestamp proving that the process is alive."""

    def __init__(self, path: str, interval: int = DEFAULT_INTERVAL):
        self.path = path
        self.interval = interval
        self.logger = get_logger(self.__class__.__name__)

    def run(self):
        """Run the heartbeat loop."""
        self.logger.info(
            f"Process heartbeat started with {self.interval}s interval."
        )

        while True:
            try:
                with open(self.path, "w") as file:
                    file.write(str(time.time()))
            except Exception:
                self.logger.error(
                    "Failed to update process heartbeat."
                )

            time.sleep(self.interval)