"""
Redis client for caching and session management.

This module provides Redis connection management and utility functions
for caching AI responses, session data, and model metadata.
"""

import json
import pickle
from typing import Any, Optional, Union
from contextlib import asynccontextmanager

import aioredis
import redis.asyncio as redis
from redis.exceptions import RedisError

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client wrapper with connection pooling and error handling."""
    
    def __init__(self):
        self.settings = get_settings()
        self._redis: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
    
    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        try:
            # Parse Redis URL
            redis_url = self.settings.redis_url
            
            # Create connection pool
            self._connection_pool = redis.ConnectionPool.from_url(
                redis_url,
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                max_connections=self.settings.redis_max_connections,
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            
            # Create Redis client
            self._redis = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self._redis.ping()
            logger.info("Redis connection established", 
                       url=redis_url, db=self.settings.redis_db)
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
        
        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None
        
        logger.info("Redis connection closed")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self._redis:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._redis
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Redis key
            value: Value to store (will be serialized)
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Set with optional TTL
            if ttl:
                result = await self.client.setex(key, ttl, serialized_value)
            else:
                result = await self.client.set(key, serialized_value)
            
            return bool(result)
            
        except RedisError as e:
            logger.error("Redis set error", key=key, error=str(e))
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            default: Default value if key not found
            
        Returns:
            Deserialized value or default
        """
        try:
            value = await self.client.get(key)
            if value is None:
                return default
            
            # Try to deserialize as JSON first
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return value
                
        except RedisError as e:
            logger.error("Redis get error", key=key, error=str(e))
            return default
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: Redis key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            result = await self.client.delete(key)
            return bool(result)
        except RedisError as e:
            logger.error("Redis delete error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Redis key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            result = await self.client.exists(key)
            return bool(result)
        except RedisError as e:
            logger.error("Redis exists error", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Redis key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.client.expire(key, ttl)
            return bool(result)
        except RedisError as e:
            logger.error("Redis expire error", key=key, ttl=ttl, error=str(e))
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live for a key.
        
        Args:
            key: Redis key
            
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            return await self.client.ttl(key)
        except RedisError as e:
            logger.error("Redis TTL error", key=key, error=str(e))
            return -2
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in Redis.
        
        Args:
            key: Redis key
            amount: Amount to increment
            
        Returns:
            New value after increment
        """
        try:
            return await self.client.incrby(key, amount)
        except RedisError as e:
            logger.error("Redis incr error", key=key, amount=amount, error=str(e))
            return 0
    
    async def hset(self, key: str, field: str, value: Any) -> bool:
        """
        Set a field in a Redis hash.
        
        Args:
            key: Redis hash key
            field: Hash field
            value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            result = await self.client.hset(key, field, serialized_value)
            return True
            
        except RedisError as e:
            logger.error("Redis hset error", key=key, field=field, error=str(e))
            return False
    
    async def hget(self, key: str, field: str, default: Any = None) -> Any:
        """
        Get a field from a Redis hash.
        
        Args:
            key: Redis hash key
            field: Hash field
            default: Default value if field not found
            
        Returns:
            Deserialized value or default
        """
        try:
            value = await self.client.hget(key, field)
            if value is None:
                return default
            
            # Try to deserialize as JSON first
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return value
                
        except RedisError as e:
            logger.error("Redis hget error", key=key, field=field, error=str(e))
            return default
    
    async def hgetall(self, key: str) -> dict:
        """
        Get all fields from a Redis hash.
        
        Args:
            key: Redis hash key
            
        Returns:
            Dictionary of field-value pairs
        """
        try:
            result = await self.client.hgetall(key)
            if not result:
                return {}
            
            # Try to deserialize values
            deserialized = {}
            for field, value in result.items():
                try:
                    deserialized[field] = json.loads(value)
                except json.JSONDecodeError:
                    deserialized[field] = value
            
            return deserialized
            
        except RedisError as e:
            logger.error("Redis hgetall error", key=key, error=str(e))
            return {}
    
    async def keys(self, pattern: str) -> list:
        """
        Get keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "cache:*")
            
        Returns:
            List of matching keys
        """
        try:
            return await self.client.keys(pattern)
        except RedisError as e:
            logger.error("Redis keys error", pattern=pattern, error=str(e))
            return []
    
    async def flushdb(self) -> bool:
        """
        Clear all keys from the current database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.client.flushdb()
            logger.info("Redis database flushed")
            return True
        except RedisError as e:
            logger.error("Redis flushdb error", error=str(e))
            return False
    
    async def info(self) -> dict:
        """
        Get Redis server information.
        
        Returns:
            Dictionary with Redis info
        """
        try:
            return await self.client.info()
        except RedisError as e:
            logger.error("Redis info error", error=str(e))
            return {}


# Global Redis client instance
redis_client = RedisClient()


@asynccontextmanager
async def get_redis():
    """
    Context manager for Redis operations.
    
    Yields:
        Redis client instance
    """
    if not redis_client._redis:
        await redis_client.connect()
    
    try:
        yield redis_client
    except Exception as e:
        logger.error("Redis operation failed", error=str(e))
        raise
    finally:
        # Don't disconnect here as it's a global client
        pass


async def init_redis() -> None:
    """Initialize Redis connection."""
    await redis_client.connect()


async def close_redis() -> None:
    """Close Redis connection."""
    await redis_client.disconnect() 