#!/usr/bin/env python3
"""
Centralized logging configuration for Python servers.
Provides simple, file-based logging with configurable levels.
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logging():
    """
    Set up centralized logging for the application.

    Configurable via environment variables:
    - LOG_LEVEL: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
    - LOG_FILE: Path to log file (default: logs/app.log)
    - LOG_TO_CONSOLE: true|false (default: true)
    - LOG_ROTATION_WHEN: When to rotate logs (default: MIDNIGHT)
    - LOG_BACKUP_COUNT: Number of backup files to keep (default: 10)

    Returns:
        Configured root logger
    """
    # Get configuration from environment variables
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    log_to_console = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
    rotation_when = os.getenv('LOG_ROTATION_WHEN', 'MIDNIGHT')
    backup_count = int(os.getenv('LOG_BACKUP_COUNT', '10'))

    # Ensure logs directory exists
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Validate log level
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        print(f"Warning: Invalid LOG_LEVEL '{log_level}', using INFO")
        log_level = 'INFO'

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Formatter for consistent log format
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Timed rotating file handler
    file_handler = TimedRotatingFileHandler(
        log_file,
        when=rotation_when,
        interval=1,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Optional console handler for development/debugging
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Log the setup
    logger.info(f"Logging initialized: level={log_level}, file={log_file}, rotation={rotation_when}, backups={backup_count}, console={log_to_console}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)