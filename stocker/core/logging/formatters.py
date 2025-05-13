"""Logging formatters for STOCKER Pro.

This module provides custom formatters for logging, including JSON formatting
for structured logging in production environments.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging.
    
    This formatter outputs log records as JSON objects, which is useful for
    log aggregation and analysis in production environments.
    
    Args:
        time_format: Format string for timestamps
        json_indent: Number of spaces for JSON indentation (None for compact JSON)
        json_ensure_ascii: Whether to escape non-ASCII characters
    """
    def __init__(
        self, 
        time_format: str = "%Y-%m-%d %H:%M:%S", 
        json_indent: Optional[int] = None,
        json_ensure_ascii: bool = False
    ):
        super().__init__()
        self.time_format = time_format
        self.json_indent = json_indent
        self.json_ensure_ascii = json_ensure_ascii
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).strftime(self.time_format),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        if hasattr(record, "extra") and record.extra:
            log_data["extra"] = record.extra
        
        return json.dumps(
            log_data, 
            indent=self.json_indent, 
            ensure_ascii=self.json_ensure_ascii
        )
