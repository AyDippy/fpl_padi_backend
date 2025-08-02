import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler

# Define the logs directory and ensure it exists
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Get a logger instance for your application
logger = logging.getLogger("fpl_padi_backend")
logger.setLevel(logging.DEBUG)
logger.propagate = False # Prevent the log from being passed to the root logger

# Formatter to define the log message format
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if not logger.handlers:
    # Handler for terminal output
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Handler for writing to a file (rotates daily)
    file_handler = TimedRotatingFileHandler(
        os.path.join(LOGS_DIR, "app.log"), when="midnight", interval=1, backupCount=7
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)