"""In-memory cache implementation for STOCKER Pro.

This module provides an in-memory cache implementation for environments
where Redis is not available.
"""

import threading
import time
from typing import Any, Dict, List, Optional, TypeVar, Union

from stocker.core.logging import get_logger
from stocker.infrastructure.cache.base import CacheInterface

# Initialize logger
logger = get_logger(__name__)

T = TypeVar('T')


class CacheItem:
    """Cache item with expiration time."""
    
    def __init__(self, value: Any, expires_at: Optional[float] = None):
        """Initialize cache item.
        
        Args:
            value: Cached value
            expires_at: Expiration timestamp, or None for no expiration
        """
        self.value = value
        self.expires_at = expires_at
    
    def is_expired(self) -> bool:
        """Check if the item is expired.
        
        Returns:
            bool: True if expired, False otherwise
        """
        return self.expires_at is not None and time.time() > self.expires_at


class MemoryCache(CacheInterface[T]):
    """In-memory cache implementation.
    
    This class implements the cache interface using an in-memory dictionary.
    It is suitable for development and testing environments, or for small
    applications where Redis is not available.
    """
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 60):
        """Initialize in-memory cache.
        
        Args:
            max_size: Maximum number of items in the cache
            cleanup_interval: Interval in seconds for cleaning up expired items
        """
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._cache: Dict[str, CacheItem] = {}
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        
        logger.info("In-memory cache initialized successfully")
    
    def _cleanup(self, force: bool = False) -> None:
        """Clean up expired items.
        
        Args:
            force: Force cleanup regardless of interval
        """
        now = time.time()
        if not force and now - self._last_cleanup < self.cleanup_interval:
            return
        
        with self._lock:
            # Clean up expired items
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            
            # If still over max size, remove oldest items
            if len(self._cache) > self.max_size:
                # Sort by expiration time (None last)
                sorted_items = sorted(
                    self._cache.items(),
                    key=lambda x: x[1].expires_at or float('inf')
                )
                # Remove oldest items
                for key, _ in sorted_items[:len(self._cache) - self.max_size]:
                    del self._cache[key]
            
            self._last_cleanup = now
    
    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[T]: Cached value or None if not found or expired
        """
        self._cleanup()
        
        with self._lock:
            item = self._cache.get(key)
            if item is None or item.is_expired():
                if item is not None and item.is_expired():
                    del self._cache[key]
                return None
            return item.value
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds, or None for no expiration
            
        Returns:
            bool: True if successful, False otherwise
        """
        self._cleanup()
        
        with self._lock:
            # Check if we need to make room
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Force cleanup to try to make room
                self._cleanup(force=True)
                
                # If still full, remove oldest item
                if len(self._cache) >= self.max_size:
                    oldest_key = min(
                        self._cache.items(),
                        key=lambda x: x[1].expires_at or float('inf')
                    )[0]
                    del self._cache[oldest_key]
            
            # Set the item
            expires_at = time.time() + ttl if ttl is not None else None
            self._cache[key] = CacheItem(value, expires_at)
            return True
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists and is not expired, False otherwise
        """
        return self.get(key) is not None
    
    def clear(self) -> bool:
        """Clear the entire cache.
        
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            self._cache.clear()
            self._last_cleanup = time.time()
            return True
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in the cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            int: New value
            
        Raises:
            ValueError: If the value is not numeric
        """
        with self._lock:
            item = self._cache.get(key)
            if item is None or item.is_expired():
                # Initialize with amount
                self.set(key, amount)
                return amount
            
            # Check if value is numeric
            if not isinstance(item.value, (int, float)):
                raise ValueError(f"Cannot increment non-numeric value for key {key}")
            
            # Increment and update
            new_value = item.value + amount
            item.value = new_value
            return new_value
    
    def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement a numeric value in the cache.
        
        Args:
            key: Cache key
            amount: Amount to decrement by
            
        Returns:
            int: New value
            
        Raises:
            ValueError: If the value is not numeric
        """
        return self.increment(key, -amount)
    
    def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict[str, T]: Dictionary of key-value pairs for found keys
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, mapping: Dict[str, T], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache.
        
        Args:
            mapping: Dictionary of key-value pairs to cache
            ttl: Time to live in seconds, or None for no expiration
            
        Returns:
            bool: True if all successful, False otherwise
        """
        for key, value in mapping.items():
            self.set(key, value, ttl)
        return True
    
    def delete_many(self, keys: List[str]) -> bool:
        """Delete multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            bool: True if all successful, False otherwise
        """
        for key in keys:
            self.delete(key)
        return True
    
    def get_or_set(self, key: str, default: callable, ttl: Optional[int] = None) -> T:
        """Get a value from the cache or set it if not found.
        
        Args:
            key: Cache key
            default: Callable that returns the default value
            ttl: Time to live in seconds, or None for no expiration
            
        Returns:
            T: Cached value or default value
        """
        value = self.get(key)
        if value is None:
            value = default()
            self.set(key, value, ttl)
        return value
    
    def touch(self, key: str, ttl: Optional[int] = None) -> bool:
        """Update the TTL of a cache key.
        
        Args:
            key: Cache key
            ttl: New time to live in seconds, or None for no expiration
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            item = self._cache.get(key)
            if item is None or item.is_expired():
                return False
            
            # Update expiration
            item.expires_at = time.time() + ttl if ttl is not None else None
            return True
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get the TTL of a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[int]: TTL in seconds, or None if no expiration or key not found
        """
        with self._lock:
            item = self._cache.get(key)
            if item is None or item.is_expired():
                return None
            
            if item.expires_at is None:
                return None
            
            ttl = int(item.expires_at - time.time())
            return ttl if ttl > 0 else None
