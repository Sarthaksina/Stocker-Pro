"""Redis cache implementation for STOCKER Pro.

This module provides a Redis-based cache implementation.
"""

import json
import pickle
from typing import Any, Dict, List, Optional, TypeVar, Union

import redis
from redis.exceptions import RedisError

from stocker.core.logging import get_logger
from stocker.infrastructure.cache.base import CacheInterface

# Initialize logger
logger = get_logger(__name__)

T = TypeVar('T')


class RedisCache(CacheInterface[T]):
    """Redis cache implementation.
    
    This class implements the cache interface using Redis.
    """
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        db: int = 0, 
        password: Optional[str] = None,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        max_connections: int = 10,
        prefix: str = "stocker:",
        serializer: str = "pickle",  # "pickle" or "json"
        url: Optional[str] = None
    ):
        """Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            max_connections: Maximum number of connections in the pool
            prefix: Key prefix
            serializer: Serializer to use ("pickle" or "json")
            url: Redis URL (overrides other connection parameters if provided)
        """
        self.prefix = prefix
        self.serializer = serializer
        
        # Create Redis connection pool
        try:
            if url:
                self.redis = redis.from_url(
                    url,
                    socket_timeout=socket_timeout,
                    socket_connect_timeout=socket_connect_timeout,
                    retry_on_timeout=retry_on_timeout,
                    decode_responses=False
                )
            else:
                connection_pool = redis.ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    socket_timeout=socket_timeout,
                    socket_connect_timeout=socket_connect_timeout,
                    retry_on_timeout=retry_on_timeout,
                    max_connections=max_connections,
                    decode_responses=False
                )
                self.redis = redis.Redis(connection_pool=connection_pool)
            
            # Test connection
            self.redis.ping()
            logger.info("Redis cache initialized successfully")
        except RedisError as e:
            logger.error(f"Failed to initialize Redis cache: {str(e)}")
            raise
    
    def _prefix_key(self, key: str) -> str:
        """Add prefix to key.
        
        Args:
            key: Cache key
            
        Returns:
            str: Prefixed key
        """
        return f"{self.prefix}{key}"
    
    def _serialize(self, value: T) -> bytes:
        """Serialize value.
        
        Args:
            value: Value to serialize
            
        Returns:
            bytes: Serialized value
        """
        if self.serializer == "json":
            return json.dumps(value).encode("utf-8")
        else:  # pickle
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> T:
        """Deserialize value.
        
        Args:
            value: Value to deserialize
            
        Returns:
            T: Deserialized value
        """
        if value is None:
            return None
        
        if self.serializer == "json":
            return json.loads(value.decode("utf-8"))
        else:  # pickle
            return pickle.loads(value)
    
    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[T]: Cached value or None if not found
        """
        try:
            value = self.redis.get(self._prefix_key(key))
            return self._deserialize(value) if value else None
        except RedisError as e:
            logger.error(f"Redis get error: {str(e)}")
            return None
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds, or None for no expiration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            serialized = self._serialize(value)
            return bool(self.redis.set(self._prefix_key(key), serialized, ex=ttl))
        except RedisError as e:
            logger.error(f"Redis set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return bool(self.redis.delete(self._prefix_key(key)))
        except RedisError as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            return bool(self.redis.exists(self._prefix_key(key)))
        except RedisError as e:
            logger.error(f"Redis exists error: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Clear the entire cache.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all keys with prefix
            keys = self.redis.keys(f"{self.prefix}*")
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except RedisError as e:
            logger.error(f"Redis clear error: {str(e)}")
            return False
    
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
        try:
            return self.redis.incrby(self._prefix_key(key), amount)
        except RedisError as e:
            logger.error(f"Redis increment error: {str(e)}")
            raise ValueError(f"Failed to increment key {key}: {str(e)}")
    
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
        try:
            return self.redis.decrby(self._prefix_key(key), amount)
        except RedisError as e:
            logger.error(f"Redis decrement error: {str(e)}")
            raise ValueError(f"Failed to decrement key {key}: {str(e)}")
    
    def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict[str, T]: Dictionary of key-value pairs for found keys
        """
        if not keys:
            return {}
        
        try:
            prefixed_keys = [self._prefix_key(key) for key in keys]
            values = self.redis.mget(prefixed_keys)
            
            result = {}
            for i, key in enumerate(keys):
                if values[i] is not None:
                    result[key] = self._deserialize(values[i])
            
            return result
        except RedisError as e:
            logger.error(f"Redis get_many error: {str(e)}")
            return {}
    
    def set_many(self, mapping: Dict[str, T], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache.
        
        Args:
            mapping: Dictionary of key-value pairs to cache
            ttl: Time to live in seconds, or None for no expiration
            
        Returns:
            bool: True if all successful, False otherwise
        """
        if not mapping:
            return True
        
        try:
            pipeline = self.redis.pipeline()
            for key, value in mapping.items():
                serialized = self._serialize(value)
                pipeline.set(self._prefix_key(key), serialized, ex=ttl)
            
            results = pipeline.execute()
            return all(results)
        except RedisError as e:
            logger.error(f"Redis set_many error: {str(e)}")
            return False
    
    def delete_many(self, keys: List[str]) -> bool:
        """Delete multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            bool: True if all successful, False otherwise
        """
        if not keys:
            return True
        
        try:
            prefixed_keys = [self._prefix_key(key) for key in keys]
            return bool(self.redis.delete(*prefixed_keys))
        except RedisError as e:
            logger.error(f"Redis delete_many error: {str(e)}")
            return False
    
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
        try:
            if ttl is None:
                # Redis doesn't support removing TTL with touch, so we need to get and set
                value = self.redis.get(self._prefix_key(key))
                if value is None:
                    return False
                return bool(self.redis.set(self._prefix_key(key), value))
            else:
                return bool(self.redis.expire(self._prefix_key(key), ttl))
        except RedisError as e:
            logger.error(f"Redis touch error: {str(e)}")
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get the TTL of a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[int]: TTL in seconds, or None if no expiration or key not found
        """
        try:
            ttl = self.redis.ttl(self._prefix_key(key))
            return ttl if ttl > 0 else None
        except RedisError as e:
            logger.error(f"Redis get_ttl error: {str(e)}")
            return None
