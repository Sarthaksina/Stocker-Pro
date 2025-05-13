"""Logging handlers for STOCKER Pro.

This module provides custom handlers for logging to different outputs
such as console, files, and potentially external services.
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

from stocker.core.logging.formatters import JsonFormatter


def get_console_handler(
    level: int = logging.INFO,
    formatter: Optional[logging.Formatter] = None,
    use_json: bool = False
) -> logging.StreamHandler:
    """Get a console handler for logging.
    
    Args:
        level: Logging level
        formatter: Custom formatter (if None, a default formatter will be used)
        use_json: Whether to use JSON formatting
        
    Returns:
        Console handler configured with the specified formatter and level
    """
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    if formatter is None:
        if use_json:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
    
    console_handler.setFormatter(formatter)
    return console_handler


def get_file_handler(
    log_file: str,
    level: int = logging.INFO,
    formatter: Optional[logging.Formatter] = None,
    use_json: bool = False,
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5,
    when: str = "midnight",
    use_timed_rotation: bool = True
) -> logging.Handler:
    """Get a file handler for logging.
    
    Args:
        log_file: Path to log file
        level: Logging level
        formatter: Custom formatter (if None, a default formatter will be used)
        use_json: Whether to use JSON formatting
        max_bytes: Maximum file size before rotation (for RotatingFileHandler)
        backup_count: Number of backup files to keep
        when: When to rotate logs (for TimedRotatingFileHandler)
        use_timed_rotation: Whether to use time-based rotation instead of size-based
        
    Returns:
        File handler configured with the specified formatter and level
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    
    if use_timed_rotation:
        file_handler = TimedRotatingFileHandler(
            log_file,
            when=when,
            backupCount=backup_count
        )
    else:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
    
    file_handler.setLevel(level)
    
    if formatter is None:
        if use_json:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
    
    file_handler.setFormatter(formatter)
    return file_handler
