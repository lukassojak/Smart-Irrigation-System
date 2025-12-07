import logging
import os
from collections import deque
from logging.handlers import TimedRotatingFileHandler


# ===========================================================================================================
# Logger Configuration
# ===========================================================================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
LOG_DIR  = os.path.join(BASE_DIR, "runtime", "node", "logs")
LOG_FILE = os.path.join(LOG_DIR, "system_log.log")

ROTATION_WHEN = 'midnight'  # Rotate logs at midnight
ROTATION_INTERVAL = 1      # Rotate every day
ROTATION_BACKUP_COUNT = 30  # Keep last 30 log files



# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# lFormatter - common format for all handlers
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')

# Singleton handler for Dashboard (DashboardLogHandler)
_dashboard_log_handler = None




class DashboardLogHandler(logging.Handler):
    def __init__(self, max_logs=5):
        super().__init__()
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.logs.append((record.levelname, msg))
        except Exception:
            self.handleError(record)


def get_dashboard_log_handler(max_logs=5):
    global _dashboard_log_handler
    if _dashboard_log_handler is None:
        _dashboard_log_handler = DashboardLogHandler(max_logs=max_logs)
        _dashboard_log_handler.setFormatter(formatter)
        _dashboard_log_handler.setLevel(logging.INFO)
    return _dashboard_log_handler


# Rotating File Handler - rotates logs daily, keeps 30 files
file_handler = TimedRotatingFileHandler(
    LOG_FILE,
    when=ROTATION_WHEN,
    interval=ROTATION_INTERVAL,
    backupCount=ROTATION_BACKUP_COUNT,
    encoding='utf-8',
    delay=True                          # Delay file creation until first log write
)

file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)  # Set file handler to log DEBUG and above

# Optional Console Handler - logs WARNING and above to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.WARNING)  # Set console handler to log WARNING and above



def get_logger(name: str) -> logging.Logger:
    """Returns a logger with the specified name, configured with file and dashboard handlers."""
    logger = logging.getLogger(name)
    if not logger.handlers:  # Prevent duplicate handlers
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        # Commenting out console handler to reduce console clutter when using CLI
        # logger.addHandler(console_handler)
        logger.addHandler(get_dashboard_log_handler())  # Attach shared DashboardLogHandler
        logger.propagate = False  # Prevent log duplication up the hierarchy
    else:
        #  Diagnostic print to verify handlers
        print(f"[DEBUG] Logger '{name}' already has handlers: {[type(h).__name__ for h in logger.handlers]}")

    return logger
