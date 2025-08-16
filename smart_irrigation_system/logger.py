import logging
import os

# Log file path
LOG_FILE = "irrigation_system_log.log"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        pass  # Create the file if it doesn't exist

# log format
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')

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
        logger.propagate = False  # Prevent log duplication up the hierarchy
    return logger