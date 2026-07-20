import logging
import os
from logging.handlers import TimedRotatingFileHandler


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
LOG_DIR  = os.path.join(BASE_DIR, "runtime", "server", "logs")
LOG_FILE = os.path.join(LOG_DIR, "system_log.log")

def setup_server_logger():
    """Initializes server logging system with rotation and unified format.
    Falls back to console-only logging if file permissions fail."""
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.handlers:
        return

    # Try to create log directory and set up file handler
    file_handler_created = False
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)
        
        # --- File handler (rotating daily) ---
        file_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", backupCount=30, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        file_handler_created = True
    except (PermissionError, OSError) as e:
        # Log to console about the file handler failure
        console_handler_temp = logging.StreamHandler()
        console_handler_temp.setFormatter(
            logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(console_handler_temp)
        logger.warning(f"Could not initialize file logging at {LOG_FILE}: {e}. Using console-only logging.")

    # --- Console handler (for real-time view) ---
    if file_handler_created or not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info("Server logger initialized.")
    return logger

setup_server_logger()


def get_logger(name: str):
    """Returns a logger instance consistent with system-wide format."""
    return logging.getLogger(name)
