import logging
import os
from logging.handlers import TimedRotatingFileHandler


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
LOG_DIR  = os.path.join(BASE_DIR, "runtime", "server", "logs")
LOG_FILE = os.path.join(LOG_DIR, "system_log.log")

def setup_server_logger():
    """Initializes server logging system with rotation and unified format."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.handlers:
        return

    # --- File handler (rotating daily) ---
    file_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", backupCount=30, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # --- Console handler (for real-time view) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("Server logger initialized.")
    return logger

setup_server_logger()


def get_logger(name: str):
    """Returns a logger instance consistent with system-wide format."""
    return logging.getLogger(name)
