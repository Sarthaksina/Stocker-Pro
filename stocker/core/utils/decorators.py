"""Decorator utilities for STOCKER Pro.

This module provides decorators for common patterns such as timing, retrying,
caching, and logging function executions.
"""

import functools
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from stocker.core.exceptions import StockerException

# Type variable for function return type
T = TypeVar('T')

# Simple in-memory cache for the cache_result decorator
_CACHE: Dict[str, Dict[str, Any]] = {}


def timer(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to measure and log the execution time of a function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that logs execution time
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            logger.debug(
                f"Function {func.__name__} executed in {end_time - start_time:.4f} seconds"
            )
            return result
        except Exception as e:
            end_time = time.time()
            logger.error(
                f"Function {func.__name__} failed after {end_time - start_time:.4f} seconds: {str(e)}"
            )
            raise
    
    return wrapper


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (in seconds)
        backoff_factor: Factor to increase delay between attempts
        exceptions: Exception types to catch and retry
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            logger = logging.getLogger(func.__module__)
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} for {func.__name__} failed: {str(e)}"
                    )
                    
                    if attempt < max_attempts:
                        logger.info(f"Retrying in {current_delay:.2f} seconds...")
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
            
            # If we get here, all attempts failed
            logger.error(f"All {max_attempts} attempts for {func.__name__} failed")
            if last_exception:
                raise last_exception
            
            # This should never happen, but just in case
            raise StockerException(f"All {max_attempts} attempts for {func.__name__} failed")
        
        return wrapper
    
    return decorator


def cache_result(
    ttl: Optional[int] = 3600,  # Time to live in seconds (1 hour default)
    max_size: int = 100,  # Maximum number of cached results
    key_func: Optional[Callable[..., str]] = None  # Function to generate cache key
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to cache function results in memory.
    
    Args:
        ttl: Time to live for cached results (in seconds, None for no expiration)
        max_size: Maximum number of cached results
        key_func: Function to generate cache key (default: based on args and kwargs)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache_name = f"{func.__module__}.{func.__name__}"
        
        if cache_name not in _CACHE:
            _CACHE[cache_name] = {}
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key based on args and kwargs
                arg_str = ",".join(str(arg) for arg in args)
                kwarg_str = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{arg_str}|{kwarg_str}"
            
            cache = _CACHE[cache_name]
            
            # Check if result is in cache and not expired
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if ttl is None or datetime.now() - timestamp < timedelta(seconds=ttl):
                    return result
            
            # If cache is full, remove oldest entry
            if len(cache) >= max_size:
                oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                del cache[oldest_key]
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, datetime.now())
            
            return result
        
        return wrapper
    
    return decorator


def log_execution(
    level: int = logging.INFO,
    log_args: bool = True,
    log_result: bool = False,
    log_exceptions: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to log function execution.
    
    Args:
        level: Logging level
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_exceptions: Whether to log exceptions
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            logger = logging.getLogger(func.__module__)
            func_name = func.__name__
            
            # Log function call with arguments if requested
            if log_args:
                arg_str = ", ".join(str(arg) for arg in args)
                kwarg_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                logger.log(level, f"Calling {func_name}({arg_str}, {kwarg_str})")
            else:
                logger.log(level, f"Calling {func_name}")
            
            try:
                result = func(*args, **kwargs)
                
                # Log function result if requested
                if log_result:
                    logger.log(level, f"{func_name} returned: {result}")
                else:
                    logger.log(level, f"{func_name} completed successfully")
                
                return result
            except Exception as e:
                # Log exception if requested
                if log_exceptions:
                    logger.exception(f"{func_name} raised an exception: {str(e)}")
                raise
        
        return wrapper
    
    return decorator
