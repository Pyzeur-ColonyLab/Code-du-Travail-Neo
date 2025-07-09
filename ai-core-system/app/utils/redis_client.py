"""
Redis client utility for the AI Core System.

This module provides async Redis connection management with connection pooling,
caching utilities, and health monitoring.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
import aioredis
from aioredis import Redis, ConnectionPool

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client with connection pooling and utility methods."""
    
    def __init__(self):
        """Initialize Redis client."""
        self.settings = get_settings()
        self._redis: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Establish Redis connection with connection pooling."""
        try:
            if self._connected:
                return
            
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                self.settings.redis_url,
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                max_connections=self.settings.redis_max_connections,
                decode_responses=True,
            )
            
            # Create Redis client
            self._redis = Redis(connection_pool=self._pool)
            
            # Test connection
            await self._redis.ping()
            self._connected = True
            
            logger.info(
                "Redis connection established",
                url=self.settings.redis_url,
                max_connections=self.settings.redis_max_connections,
            )
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        try:
            if self._redis:
                await self._redis.close()
            if self._pool:
                await self._pool.disconnect()
            
            self._connected = False
            logger.info("Redis connection closed")
            
        except Exception as e:
            logger.error("Error closing Redis connection", error=str(e))
    
    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            if not self._redis:
                return False
            
            await self._redis.ping()
            return True
            
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False
    
    async def get(self, key: str, deserialize: bool = True, default: Any = None) -> Any:
        """Get value from Redis."""
        try:
            if not self._redis:
                return default
            
            value = await self._redis.get(key)
            if value is None:
                return default
            
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                return value
                
        except Exception as e:
            logger.error("Redis get error", key=key, error=str(e))
            return default
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None, serialize: bool = True) -> bool:
        """Set value in Redis."""
        try:
            if not self._redis:
                return False
            
            if serialize and not isinstance(value, (str, bytes)):
                value = json.dumps(value)
            
            await self._redis.set(key, value, ex=expire)
            return True
            
        except Exception as e:
            logger.error("Redis set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            if not self._redis:
                return False
            
            result = await self._redis.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error("Redis delete error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            if not self._redis:
                return False
            
            result = await self._redis.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error("Redis exists error", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        try:
            if not self._redis:
                return False
            
            result = await self._redis.expire(key, seconds)
            return result
            
        except Exception as e:
            logger.error("Redis expire error", key=key, error=str(e))
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in Redis."""
        try:
            if not self._redis:
                return None
            
            result = await self._redis.incr(key, amount)
            return result
            
        except Exception as e:
            logger.error("Redis incr error", key=key, error=str(e))
            return None
    
    async def hget(self, key: str, field: str, deserialize: bool = True, default: Any = None) -> Any:
        """Get hash field value from Redis."""
        try:
            if not self._redis:
                return default
            
            value = await self._redis.hget(key, field)
            if value is None:
                return default
            
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                return value
                
        except Exception as e:
            logger.error("Redis hget error", key=key, field=field, error=str(e))
            return default
    
    async def hset(self, key: str, field: str, value: Any, serialize: bool = True) -> bool:
        """Set hash field value in Redis."""
        try:
            if not self._redis:
                return False
            
            if serialize and not isinstance(value, (str, bytes)):
                value = json.dumps(value)
            
            await self._redis.hset(key, field, value)
            return True
            
        except Exception as e:
            logger.error("Redis hset error", key=key, field=field, error=str(e))
            return False
    
    async def hgetall(self, key: str, deserialize: bool = True) -> Dict[str, Any]:
        """Get all hash fields from Redis."""
        try:
            if not self._redis:
                return {}
            
            data = await self._redis.hgetall(key)
            if not data:
                return {}
            
            if deserialize:
                result = {}
                for field, value in data.items():
                    try:
                        result[field] = json.loads(value)
                    except json.JSONDecodeError:
                        result[field] = value
                return result
            else:
                return data
                
        except Exception as e:
            logger.error("Redis hgetall error", key=key, error=str(e))
            return {}
    
    async def lpush(self, key: str, *values: Any, serialize: bool = True) -> Optional[int]:
        """Push values to the left of a list."""
        try:
            if not self._redis:
                return None
            
            if serialize:
                serialized_values = []
                for value in values:
                    if not isinstance(value, (str, bytes)):
                        serialized_values.append(json.dumps(value))
                    else:
                        serialized_values.append(value)
                values = serialized_values
            
            result = await self._redis.lpush(key, *values)
            return result
            
        except Exception as e:
            logger.error("Redis lpush error", key=key, error=str(e))
            return None
    
    async def rpop(self, key: str, deserialize: bool = True) -> Any:
        """Pop value from the right of a list."""
        try:
            if not self._redis:
                return None
            
            value = await self._redis.rpop(key)
            if value is None:
                return None
            
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                return value
                
        except Exception as e:
            logger.error("Redis rpop error", key=key, error=str(e))
            return None
    
    async def llen(self, key: str) -> int:
        """Get length of a list."""
        try:
            if not self._redis:
                return 0
            
            result = await self._redis.llen(key)
            return result
            
        except Exception as e:
            logger.error("Redis llen error", key=key, error=str(e))
            return 0
    
    async def cache_get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with automatic deserialization."""
        return await self.get(f"cache:{key}", deserialize=True, default=default)
    
    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with automatic serialization and TTL."""
        return await self.set(f"cache:{key}", value, expire=ttl, serialize=True)
    
    async def cache_delete(self, key: str) -> bool:
        """Delete value from cache."""
        return await self.delete(f"cache:{key}")
    
    async def session_get(self, session_id: str, default: Any = None) -> Any:
        """Get session data."""
        return await self.get(f"session:{session_id}", deserialize=True, default=default)
    
    async def session_set(self, session_id: str, data: Any, ttl: int = 3600) -> bool:
        """Set session data with TTL."""
        return await self.set(f"session:{session_id}", data, expire=ttl, serialize=True)
    
    async def session_delete(self, session_id: str) -> bool:
        """Delete session data."""
        return await self.delete(f"session:{session_id}")
    
    async def rate_limit_check(self, key: str, limit: int, window: int = 60) -> bool:
        """Check rate limit for a key."""
        try:
            current = await self.get(key, deserialize=False, default=0)
            current = int(current) if current else 0
            
            if current >= limit:
                return False
            
            await self.incr(key)
            await self.expire(key, window)
            return True
            
        except Exception as e:
            logger.error("Rate limit check error", key=key, error=str(e))
            return False
    
    async def get_memory_info(self) -> Dict[str, Any]:
        """Get Redis memory information."""
        try:
            if not self._redis:
                return {}
            
            info = await self._redis.info("memory")
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "used_memory_rss": info.get("used_memory_rss", 0),
                "used_memory_rss_human": info.get("used_memory_rss_human", "0B"),
            }
            
        except Exception as e:
            logger.error("Redis memory info error", error=str(e))
            return {}


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get the global Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    
    return _redis_client 