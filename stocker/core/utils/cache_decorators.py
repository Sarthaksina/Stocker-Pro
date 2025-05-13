"""Cache decorators for STOCKER Pro.

This module provides decorators for caching function results.
"""

import functools
import hashlib
import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

from stocker.core.logging import get_logger
from stocker.infrastructure.cache import get_cache

# Initialize logger
logger = get_logger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def _generate_cache_key(func: Callable, args: Tuple, kwargs: Dict) -> str:
    """Generate a cache key for a function call.
    
    Args:
        func: Function being called
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        str: Cache key
    """
    # Get function name and module
    func_name = func.__name__
    module_name = func.__module__
    
    # Convert args and kwargs to JSON-serializable format
    try:
        args_str = json.dumps(args, sort_keys=True)
        kwargs_str = json.dumps(kwargs, sort_keys=True)
    except (TypeError, ValueError):
        # If args/kwargs contain non-serializable objects, use their string representation
        args_str = str(args)
        kwargs_str = str(kwargs)
    
    # Create key components
    key_parts = [module_name, func_name, args_str, kwargs_str]
    key_str = ":".join(key_parts)
    
    # Hash the key to make it shorter and ensure it's valid for all cache backends
    return f"cache:{hashlib.md5(key_str.encode()).hexdigest()}"


def cached(ttl: Optional[int] = None, prefix: Optional[str] = None) -> Callable[[F], F]:
    """Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds, or None for no expiration
        prefix: Optional prefix for cache keys
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache instance
            cache = get_cache()
            
            # Generate cache key
            key = _generate_cache_key(func, args, kwargs)
            if prefix:
                key = f"{prefix}:{key}"
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        return cast(F, wrapper)
    
    return decorator


def cached_property(ttl: Optional[int] = None, prefix: Optional[str] = None):
    """Decorator for caching class property results.
    
    This is similar to @property and @cached combined.
    
    Args:
        ttl: Time to live in seconds, or None for no expiration
        prefix: Optional prefix for cache keys
        
    Returns:
        property: Cached property descriptor
    """
    def decorator(func):
        @property
        @functools.wraps(func)
        def wrapper(self):
            # Get cache instance
            cache = get_cache()
            
            # Generate cache key
            # Include class name and instance id in the key
            class_name = self.__class__.__name__
            instance_id = str(id(self))
            func_name = func.__name__
            
            key = f"property:{class_name}:{instance_id}:{func_name}"
            if prefix:
                key = f"{prefix}:{key}"
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for property {class_name}.{func_name}")
                return cached_result
            
            # Call function and cache result
            logger.debug(f"Cache miss for property {class_name}.{func_name}")
            result = func(self)
            cache.set(key, result, ttl)
            return result
        
        return wrapper
    
    return decorator


def invalidate_cache(func: Callable, args: Tuple = None, kwargs: Dict = None, prefix: Optional[str] = None) -> bool:
    """Invalidate cache for a function call.
    
    Args:
        func: Function whose cache to invalidate
        args: Positional arguments, or None to invalidate all calls
        kwargs: Keyword arguments, or None to invalidate all calls
        prefix: Optional prefix for cache keys
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get cache instance
    cache = get_cache()
    
    if args is None and kwargs is None:
        # Invalidate all calls to this function
        # This is a best-effort approach and may not work with all cache backends
        func_name = func.__name__
        module_name = func.__module__
        pattern = f"cache:{module_name}:{func_name}:*"
        
        # For Redis, we could use SCAN with pattern matching
        # For memory cache, we'd need to iterate through all keys
        # Since this is complex and backend-specific, we'll just log a warning
        logger.warning(f"Full cache invalidation for {module_name}.{func_name} is not fully supported")
        return False
    else:
        # Invalidate specific call
        args = args or ()
        kwargs = kwargs or {}
        key = _generate_cache_key(func, args, kwargs)
        if prefix:
            key = f"{prefix}:{key}"
        
        return cache.delete(key)
