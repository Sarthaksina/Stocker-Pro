"""Cache factory for STOCKER Pro.

This module provides a factory function to get the appropriate cache implementation
based on the application configuration.
"""

from typing import Optional, Type, TypeVar, Union

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger
from stocker.infrastructure.cache.base import CacheInterface
from stocker.infrastructure.cache.memory_cache import MemoryCache
from stocker.infrastructure.cache.redis_cache import RedisCache

# Initialize logger
logger = get_logger(__name__)

T = TypeVar('T')

# Cache instance singleton
_cache_instance = None


def get_cache(cache_type: Optional[str] = None) -> CacheInterface:
    """Get a cache instance based on configuration.
    
    This function returns a singleton cache instance based on the application
    configuration. If cache_type is provided, it overrides the configuration.
    
    Args:
        cache_type: Cache type to use ("redis" or "memory"), or None to use configuration
        
    Returns:
        CacheInterface: Cache instance
        
    Raises:
        ValueError: If cache_type is invalid
    """
    global _cache_instance
    
    # Return existing instance if available
    if _cache_instance is not None:
        return _cache_instance
    
    # Get settings
    settings = get_settings()
    
    # Determine cache type
    if cache_type is None:
        # Use configuration
        cache_type = getattr(settings, "cache_type", "memory")
    
    # Create cache instance
    if cache_type.lower() == "redis":
        # Get Redis URL from settings
        redis_url = getattr(settings, "redis_url", None)
        
        # Create Redis cache
        try:
            _cache_instance = RedisCache(url=redis_url)
            logger.info("Using Redis cache")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {str(e)}. Falling back to memory cache.")
            _cache_instance = MemoryCache()
    elif cache_type.lower() == "memory":
        # Create memory cache
        _cache_instance = MemoryCache()
        logger.info("Using in-memory cache")
    else:
        raise ValueError(f"Invalid cache type: {cache_type}. Must be 'redis' or 'memory'.")
    
    return _cache_instance
