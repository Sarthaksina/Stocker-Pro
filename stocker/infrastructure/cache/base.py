"""Base cache interface for STOCKER Pro.

This module defines the base cache interface for the application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar, Union, Generic
import time

T = TypeVar('T')


class CacheInterface(Generic[T], ABC):
    """Base cache interface.
    
    This abstract class defines the interface for all cache implementations.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[T]: Cached value or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds, or None for no expiration
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear the entire cache.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict[str, T]: Dictionary of key-value pairs for found keys
        """
        pass
    
    @abstractmethod
    def set_many(self, mapping: Dict[str, T], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache.
        
        Args:
            mapping: Dictionary of key-value pairs to cache
            ttl: Time to live in seconds, or None for no expiration
            
        Returns:
            bool: True if all successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_many(self, keys: List[str]) -> bool:
        """Delete multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            bool: True if all successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_or_set(self, key: str, default: callable, ttl: Optional[int] = None) -> T:
        """Get a value from the cache or set it if not found.
        
        Args:
            key: Cache key
            default: Callable that returns the default value
            ttl: Time to live in seconds, or None for no expiration
            
        Returns:
            T: Cached value or default value
        """
        pass
    
    @abstractmethod
    def touch(self, key: str, ttl: Optional[int] = None) -> bool:
        """Update the TTL of a cache key.
        
        Args:
            key: Cache key
            ttl: New time to live in seconds, or None for no expiration
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_ttl(self, key: str) -> Optional[int]:
        """Get the TTL of a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[int]: TTL in seconds, or None if no expiration or key not found
        """
        pass
