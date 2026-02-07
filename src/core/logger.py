"""
Centralized logging configuration for SeeSeaAgent
"""
import logging
import sys


def setup_logger(name: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup and return a configured logger

    Args:
        name: Logger name (use __name__ from calling module)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or 'seesea')

    # Only configure if not already configured
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(level)

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


# Configure APScheduler logging
def setup_apscheduler_logging(level: int = logging.DEBUG):
    """
    Configure APScheduler logging

    Args:
        level: Logging level for APScheduler (default: DEBUG)
    """
    apscheduler_logger = logging.getLogger('apscheduler')
    apscheduler_logger.setLevel(level)

    # Use same formatter as our loggers
    if not apscheduler_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] [apscheduler] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        apscheduler_logger.addHandler(handler)
        apscheduler_logger.propagate = False


# Create default logger instance
logger = setup_logger('seesea')
