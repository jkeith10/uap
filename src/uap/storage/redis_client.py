"""Redis Client for UAP"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis
from redis.asyncio import Redis
from pydantic import BaseModel, Field


class RedisConfig(BaseModel):
    """Redis configuration"""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(None, description="Redis password")
    max_connections: int = Field(default=10, description="Maximum number of connections")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(default=5, description="Socket connect timeout in seconds")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")


class RedisClient:
    """Async Redis client for UAP"""
    
    def __init__(self, config: RedisConfig):
        self.config = config
        self._redis: Optional[Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect to Redis"""
        if self._redis is None:
            self._connection_pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval
            )
            
            self._redis = Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self._redis.ping()
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
        
        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None
    
    async def ping(self) -> bool:
        """Ping Redis server"""
        try:
            result = await self._redis.ping()
            return result is True
        except Exception:
            return False
    
    # Basic operations
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key"""
        return await self._redis.get(key)
    
    async def set(
        self,
        key: str,
        value: Union[str, bytes, int, float],
        ex: Optional[Union[int, timedelta]] = None,
        px: Optional[Union[int, timedelta]] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set a key-value pair"""
        return await self._redis.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        return await self._redis.delete(*keys)
    
    async def exists(self, *keys: str) -> int:
        """Check if one or more keys exist"""
        return await self._redis.exists(*keys)
    
    async def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """Set expiration time for a key"""
        return await self._redis.expire(key, time)
    
    async def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        return await self._redis.ttl(key)
    
    # Hash operations
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get a field value from a hash"""
        return await self._redis.hget(name, key)
    
    async def hset(self, name: str, key: str = None, value: str = None, mapping: Dict[str, str] = None) -> int:
        """Set a field value in a hash"""
        if mapping:
            return await self._redis.hset(name, mapping=mapping)
        else:
            return await self._redis.hset(name, key, value)
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all field-value pairs from a hash"""
        return await self._redis.hgetall(name)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete one or more fields from a hash"""
        return await self._redis.hdel(name, *keys)
    
    async def hexists(self, name: str, key: str) -> bool:
        """Check if a field exists in a hash"""
        return await self._redis.hexists(name, key)
    
    # List operations
    async def lpush(self, name: str, *values: str) -> int:
        """Push values to the left of a list"""
        return await self._redis.lpush(name, *values)
    
    async def rpush(self, name: str, *values: str) -> int:
        """Push values to the right of a list"""
        return await self._redis.rpush(name, *values)
    
    async def lpop(self, name: str) -> Optional[str]:
        """Pop a value from the left of a list"""
        return await self._redis.lpop(name)
    
    async def rpop(self, name: str) -> Optional[str]:
        """Pop a value from the right of a list"""
        return await self._redis.rpop(name)
    
    async def llen(self, name: str) -> int:
        """Get the length of a list"""
        return await self._redis.llen(name)
    
    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """Get a range of values from a list"""
        return await self._redis.lrange(name, start, end)
    
    # Set operations
    async def sadd(self, name: str, *values: str) -> int:
        """Add values to a set"""
        return await self._redis.sadd(name, *values)
    
    async def srem(self, name: str, *values: str) -> int:
        """Remove values from a set"""
        return await self._redis.srem(name, *values)
    
    async def smembers(self, name: str) -> set:
        """Get all members of a set"""
        return await self._redis.smembers(name)
    
    async def sismember(self, name: str, value: str) -> bool:
        """Check if a value is a member of a set"""
        return await self._redis.sismember(name, value)
    
    # Stream operations
    async def xadd(self, name: str, fields: Dict[str, str], maxlen: Optional[int] = None) -> str:
        """Add an entry to a stream"""
        return await self._redis.xadd(name, fields, maxlen=maxlen)
    
    async def xread(self, streams: Dict[str, str], count: Optional[int] = None, block: Optional[int] = None) -> List:
        """Read from streams"""
        return await self._redis.xread(streams, count=count, block=block)
    
    async def xrange(self, name: str, start: str = "-", end: str = "+", count: Optional[int] = None) -> List:
        """Get a range of entries from a stream"""
        return await self._redis.xrange(name, start, end, count=count)
    
    async def xlen(self, name: str) -> int:
        """Get the length of a stream"""
        return await self._redis.xlen(name)
    
    # Pub/Sub operations
    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel"""
        return await self._redis.publish(channel, message)
    
    async def subscribe(self, *channels: str):
        """Subscribe to channels"""
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub
    
    async def unsubscribe(self, pubsub, *channels: str):
        """Unsubscribe from channels"""
        await pubsub.unsubscribe(*channels)
        await pubsub.close()
    
    # Utility operations
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern"""
        keys = await self._redis.keys(pattern)
        return [key.decode() if isinstance(key, bytes) else key for key in keys]
    
    async def scan(self, cursor: int = 0, match: Optional[str] = None, count: Optional[int] = None) -> tuple:
        """Scan for keys"""
        return await self._redis.scan(cursor, match=match, count=count)
    
    # JSON operations (using RedisJSON if available)
    async def json_set(self, name: str, path: str, obj: Any) -> bool:
        """Set a JSON object"""
        try:
            # Try RedisJSON first
            return await self._redis.execute_command("JSON.SET", name, path, json.dumps(obj))
        except Exception:
            # Fallback to regular string storage
            return await self.set(name, json.dumps(obj))
    
    async def json_get(self, name: str, path: str = ".") -> Optional[Any]:
        """Get a JSON object"""
        try:
            # Try RedisJSON first
            result = await self._redis.execute_command("JSON.GET", name, path)
            return json.loads(result) if result else None
        except Exception:
            # Fallback to regular string retrieval
            result = await self.get(name)
            return json.loads(result) if result else None
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check"""
        try:
            start_time = datetime.now(timezone.utc)
            await self.ping()
            end_time = datetime.now(timezone.utc)
            
            return {
                "status": "healthy",
                "latency_ms": (end_time - start_time).total_seconds() * 1000,
                "timestamp": end_time.isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
