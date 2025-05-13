"""Date and time utilities for STOCKER Pro.

This module provides functions for working with dates and times,
including parsing, formatting, and market-specific date operations.
"""

import datetime
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple, Union

import pandas as pd
import pytz

# Default timezone for market operations
DEFAULT_TIMEZONE = pytz.timezone("America/New_York")

# Market hours (Eastern Time)
MARKET_OPEN_TIME = time(9, 30)  # 9:30 AM ET
MARKET_CLOSE_TIME = time(16, 0)  # 4:00 PM ET

# US market holidays (incomplete, would need to be updated yearly)
US_HOLIDAYS_2025 = [
    date(2025, 1, 1),    # New Year's Day
    date(2025, 1, 20),   # Martin Luther King Jr. Day
    date(2025, 2, 17),   # Presidents' Day
    date(2025, 4, 18),   # Good Friday
    date(2025, 5, 26),   # Memorial Day
    date(2025, 6, 19),   # Juneteenth
    date(2025, 7, 4),    # Independence Day
    date(2025, 9, 1),    # Labor Day
    date(2025, 11, 27),  # Thanksgiving Day
    date(2025, 12, 25),  # Christmas Day
]


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> datetime:
    """Parse a date string into a datetime object.
    
    Args:
        date_str: Date string to parse
        fmt: Format string for parsing
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValueError: If the date string cannot be parsed
    """
    try:
        return datetime.strptime(date_str, fmt)
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected format: {fmt}") from e


def format_date(dt: Union[datetime, date], fmt: str = "%Y-%m-%d") -> str:
    """Format a datetime object as a string.
    
    Args:
        dt: Datetime object to format
        fmt: Format string for formatting
        
    Returns:
        Formatted date string
    """
    return dt.strftime(fmt)


def get_date_range(
    start_date: Union[str, datetime, date],
    end_date: Optional[Union[str, datetime, date]] = None,
    days: Optional[int] = None,
    fmt: str = "%Y-%m-%d"
) -> Tuple[datetime, datetime]:
    """Get a date range from start date to end date or for a number of days.
    
    Args:
        start_date: Start date (string or datetime)
        end_date: End date (string or datetime)
        days: Number of days from start date (used if end_date is None)
        fmt: Format string for parsing date strings
        
    Returns:
        Tuple of (start_datetime, end_datetime)
        
    Raises:
        ValueError: If neither end_date nor days is provided
    """
    # Parse start date if it's a string
    if isinstance(start_date, str):
        start_dt = parse_date(start_date, fmt)
    elif isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_dt = datetime.combine(start_date, time())
    else:
        start_dt = start_date
    
    # Calculate end date
    if end_date is not None:
        # Parse end date if it's a string
        if isinstance(end_date, str):
            end_dt = parse_date(end_date, fmt)
        elif isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_dt = datetime.combine(end_date, time())
        else:
            end_dt = end_date
    elif days is not None:
        # Calculate end date based on days
        end_dt = start_dt + timedelta(days=days)
    else:
        # Default to current date if neither end_date nor days is provided
        end_dt = datetime.now()
    
    return start_dt, end_dt


def is_market_open(
    dt: Optional[datetime] = None,
    tz: pytz.timezone = DEFAULT_TIMEZONE
) -> bool:
    """Check if the market is open at the specified datetime.
    
    Args:
        dt: Datetime to check (default: current time)
        tz: Timezone for the check
        
    Returns:
        True if the market is open, False otherwise
    """
    if dt is None:
        dt = datetime.now(tz)
    elif dt.tzinfo is None:
        dt = tz.localize(dt)
    
    # Convert to Eastern Time for market hours check
    et_dt = dt.astimezone(DEFAULT_TIMEZONE)
    
    # Check if it's a weekday
    if et_dt.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if it's a holiday
    if et_dt.date() in US_HOLIDAYS_2025:  # This should be expanded to include all relevant years
        return False
    
    # Check if it's during market hours
    et_time = et_dt.time()
    return MARKET_OPEN_TIME <= et_time < MARKET_CLOSE_TIME


def get_previous_business_day(
    dt: Optional[Union[datetime, date]] = None,
    skip_holidays: bool = True
) -> date:
    """Get the previous business day.
    
    Args:
        dt: Reference date (default: today)
        skip_holidays: Whether to skip holidays
        
    Returns:
        Previous business day
    """
    if dt is None:
        dt = date.today()
    elif isinstance(dt, datetime):
        dt = dt.date()
    
    # Start with the previous day
    prev_day = dt - timedelta(days=1)
    
    # Skip weekends
    while prev_day.weekday() >= 5:  # Saturday or Sunday
        prev_day = prev_day - timedelta(days=1)
    
    # Skip holidays if requested
    if skip_holidays:
        while prev_day in US_HOLIDAYS_2025:  # This should be expanded to include all relevant years
            prev_day = prev_day - timedelta(days=1)
            # Skip weekends again if needed
            while prev_day.weekday() >= 5:
                prev_day = prev_day - timedelta(days=1)
    
    return prev_day


def get_next_business_day(
    dt: Optional[Union[datetime, date]] = None,
    skip_holidays: bool = True
) -> date:
    """Get the next business day.
    
    Args:
        dt: Reference date (default: today)
        skip_holidays: Whether to skip holidays
        
    Returns:
        Next business day
    """
    if dt is None:
        dt = date.today()
    elif isinstance(dt, datetime):
        dt = dt.date()
    
    # Start with the next day
    next_day = dt + timedelta(days=1)
    
    # Skip weekends
    while next_day.weekday() >= 5:  # Saturday or Sunday
        next_day = next_day + timedelta(days=1)
    
    # Skip holidays if requested
    if skip_holidays:
        while next_day in US_HOLIDAYS_2025:  # This should be expanded to include all relevant years
            next_day = next_day + timedelta(days=1)
            # Skip weekends again if needed
            while next_day.weekday() >= 5:
                next_day = next_day + timedelta(days=1)
    
    return next_day
