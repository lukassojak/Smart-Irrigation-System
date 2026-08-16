import threading, time
from pathlib import Path

from smart_irrigation_system.node.utils.logger import get_logger


DEFAULT_INTERVAL = 60


class ProcessHeartbeat:
    """Periodically writes a timestamp proving that the process is alive."""

    def __init__(self, path: str, interval: int = DEFAULT_INTERVAL):
        self.path = path
        self.interval = interval
        self._stop_event = threading.Event()
        self.logger = get_logger(self.__class__.__name__)

    def run(self):
        self.logger.info(
            f"Process heartbeat started with {self.interval:.0f}s interval."
        )

        while not self._stop_event.is_set():
            self._write_heartbeat()

            if self._stop_event.wait(timeout=self.interval):
                break

        self.logger.info("Process heartbeat stopped.")

    def stop(self):
        self._stop_event.set()

    def _write_heartbeat(self):
        try:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as file:
                file.write(str(time.time()))
        except Exception:
            self.logger.error(
                "Failed to update process heartbeat."
            )