"""Logger configuration for STOCKER Pro.

This module provides functions for creating and configuring loggers
with appropriate handlers and formatters.
"""

import logging
import os
from typing import Dict, List, Optional, Union

from stocker.core.logging.handlers import get_console_handler, get_file_handler


def get_logger(
    name: str,
    level: int = logging.INFO,
    console_logging: bool = True,
    file_logging: bool = False,
    log_file: Optional[str] = None,
    use_json: bool = False
) -> logging.Logger:
    """Get a logger with the specified configuration.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level
        console_logging: Whether to log to console
        file_logging: Whether to log to file
        log_file: Path to log file (required if file_logging is True)
        use_json: Whether to use JSON formatting
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Add console handler if requested
    if console_logging:
        logger.addHandler(get_console_handler(level=level, use_json=use_json))
    
    # Add file handler if requested
    if file_logging:
        if not log_file:
            log_file = os.path.join("logs", f"{name.replace('.', '_')}.log")
        
        logger.addHandler(get_file_handler(
            log_file=log_file,
            level=level,
            use_json=use_json
        ))
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def configure_logging(
    default_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S",
    console_logging: bool = True,
    file_logging: bool = True,
    use_json: bool = False,
    module_levels: Optional[Dict[str, int]] = None
) -> None:
    """Configure global logging settings.
    
    Args:
        default_level: Default logging level
        log_file: Path to log file
        log_format: Log format string
        date_format: Date format string
        console_logging: Whether to log to console
        file_logging: Whether to log to file
        use_json: Whether to use JSON formatting
        module_levels: Dictionary mapping module names to logging levels
    """
    # Create logs directory if it doesn't exist and file_logging is enabled
    if file_logging and log_file:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(default_level)
    
    # Remove existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(log_format, date_format)
    
    # Add console handler if requested
    if console_logging:
        console_handler = get_console_handler(
            level=default_level,
            formatter=formatter,
            use_json=use_json
        )
        root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if file_logging and log_file:
        file_handler = get_file_handler(
            log_file=log_file,
            level=default_level,
            formatter=formatter,
            use_json=use_json
        )
        root_logger.addHandler(file_handler)
    
    # Set specific module levels if provided
    if module_levels:
        for module_name, level in module_levels.items():
            logging.getLogger(module_name).setLevel(level)
