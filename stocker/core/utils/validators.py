"""Validation utilities for STOCKER Pro.

This module provides functions for validating various types of data
used throughout the application, such as stock symbols, date ranges, etc.
"""

import re
from datetime import datetime
from typing import List, Optional, Tuple, Union

from stocker.core.exceptions import ValidationError
from stocker.core.utils.datetime import parse_date

# Regular expression for validating stock symbols
# Most stock symbols consist of 1-5 uppercase letters, but some may include numbers or special characters
SYMBOL_PATTERN = re.compile(r'^[A-Z0-9.\-]{1,6}$')

# Regular expression for validating email addresses
EMAIL_PATTERN = re.compile(r'^[\w\.-]+@([\w\-]+\.)+[A-Z|a-z]{2,}$')

# Valid timeframes for stock data
VALID_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1mo']


def validate_symbol(symbol: str) -> bool:
    """Validate a stock symbol.
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        True if the symbol is valid, False otherwise
    """
    if not symbol:
        return False
    
    return bool(SYMBOL_PATTERN.match(symbol))


def validate_symbols(symbols: List[str]) -> List[str]:
    """Validate a list of stock symbols and return the invalid ones.
    
    Args:
        symbols: List of stock symbols to validate
        
    Returns:
        List of invalid symbols (empty if all are valid)
    """
    return [symbol for symbol in symbols if not validate_symbol(symbol)]


def validate_date_range(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    fmt: str = "%Y-%m-%d"
) -> Tuple[bool, Optional[str]]:
    """Validate a date range.
    
    Args:
        start_date: Start date (string or datetime)
        end_date: End date (string or datetime)
        fmt: Format string for parsing date strings
        
    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if the date range is valid, False otherwise
        error_message: Error message if the date range is invalid, None otherwise
    """
    try:
        # Parse dates if they are strings
        if isinstance(start_date, str):
            start_dt = parse_date(start_date, fmt)
        else:
            start_dt = start_date
        
        if isinstance(end_date, str):
            end_dt = parse_date(end_date, fmt)
        else:
            end_dt = end_date
        
        # Check if start date is before end date
        if start_dt > end_dt:
            return False, f"Start date {start_dt} is after end date {end_dt}"
        
        # Check if end date is in the future
        if end_dt > datetime.now():
            # This is just a warning, not an error
            pass
        
        return True, None
    except ValueError as e:
        return False, str(e)


def validate_timeframe(timeframe: str) -> bool:
    """Validate a timeframe string.
    
    Args:
        timeframe: Timeframe string to validate (e.g., '1d', '1h')
        
    Returns:
        True if the timeframe is valid, False otherwise
    """
    return timeframe in VALID_TIMEFRAMES


def validate_email(email: str) -> bool:
    """Validate an email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if the email is valid, False otherwise
    """
    if not email:
        return False
    
    return bool(EMAIL_PATTERN.match(email))
