import logging
import os
from collections import deque

# Log file path
LOG_FILE = "irrigation_system_log.log"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        pass  # Create the file if it doesn't exist

# log format
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')

# Singleton DashboardLogHandler
_dashboard_log_handler = None

class DashboardLogHandler(logging.Handler):
    def __init__(self, max_logs=5):
        super().__init__()
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)

    def emit(self, record):
        msg = self.format(record)
        self.logs.append((record.levelname, msg))

def get_dashboard_log_handler(max_logs=5):
    global _dashboard_log_handler
    if _dashboard_log_handler is None:
        _dashboard_log_handler = DashboardLogHandler(max_logs=max_logs)
    return _dashboard_log_handler


# Handler - file output
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)  # Set file handler to log DEBUG and above

# Handler - console output
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.WARNING)  # Set console handler to log WARNING and above

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:  # Prevent duplicate handlers
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.addHandler(get_dashboard_log_handler())  # Attach shared DashboardLogHandler
        logger.propagate = False  # Prevent log duplication up the hierarchy
    return logger
