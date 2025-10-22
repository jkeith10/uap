"""Intelligent Caching Layer for UAP"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, Optional, TypeVar
from datetime import datetime, timezone, timedelta
from functools import wraps

from .storage.redis_client import RedisClient
from .logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class Cache:
    """Intelligent cache with Redis backend"""
    
    def __init__(self, redis_client: RedisClient, default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self._local_cache: Dict[str, tuple[Any, datetime]] = {}
        self._local_cache_ttl = 60  # Local cache TTL in seconds
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Check local cache first
        if key in self._local_cache:
            value, timestamp = self._local_cache[key]
            if datetime.now(timezone.utc) - timestamp < timedelta(seconds=self._local_cache_ttl):
                logger.debug("Cache hit (local)", key=key)
                return value
        
        # Check Redis
        redis_value = await self.redis.get(f"cache:{key}")
        if redis_value:
            value = json.loads(redis_value)
            # Store in local cache
            self._local_cache[key] = (value, datetime.now(timezone.utc))
            logger.debug("Cache hit (redis)", key=key)
            return value
        
        logger.debug("Cache miss", key=key)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        
        # Store in Redis
        await self.redis.set(
            f"cache:{key}",
            json.dumps(value, default=str),
            ex=ttl
        )
        
        # Store in local cache
        self._local_cache[key] = (value, datetime.now(timezone.utc))
        
        logger.debug("Cache set", key=key, ttl=ttl)
    
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        await self.redis.delete(f"cache:{key}")
        self._local_cache.pop(key, None)
        logger.debug("Cache delete", key=key)
    
    async def clear(self) -> None:
        """Clear all cache"""
        # Clear Redis cache keys
        keys = await self.redis.keys("cache:*")
        if keys:
            await self.redis.delete(*keys)
        
        # Clear local cache
        self._local_cache.clear()
        
        logger.info("Cache cleared")
    
    def cached(self, ttl: Optional[int] = None):
        """Decorator for caching function results"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = f"{func.__name__}:{args}:{kwargs}"
                
                # Check cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Call function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Store in cache
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator


# Global cache instance
_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Get global cache instance"""
    if _cache is None:
        raise RuntimeError("Cache not initialized")
    return _cache


def set_cache(cache: Cache) -> None:
    """Set global cache instance"""
    global _cache
    _cache = cache


def cached(ttl: Optional[int] = None):
    """Decorator for caching function results"""
    return get_cache().cached(ttl)

