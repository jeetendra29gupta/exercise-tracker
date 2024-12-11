import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logging():
    """
    Set up logging configuration for the application with a rotating log file and console output.
    """
    # Define log directory and file name
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f'tracker-app-{datetime.now().strftime("%Y-%m-%d")}.log')

    # Get log level from environment variable
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)  # Default to INFO if invalid

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Define log format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Set up log rotation for the file handler
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )  # 10 MB size limit and 5 backup files
        file_handler.setFormatter(formatter)
    except Exception as e:
        logger.error(f"Failed to set up file handler: {e}")
        raise

    # Remove existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
