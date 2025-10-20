"""Memory Bus - Unified interface for cross-session memory sharing"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Set
from uuid import UUID
from datetime import datetime, timedelta, timezone

from ..models.memory_stream import MemoryStream, MemoryQuery, MemoryGranularity, RetentionPolicy
from .redis_client import RedisClient
from .postgres_client import PostgreSQLClient


class MemoryBus:
    """Unified memory bus for cross-session memory sharing"""
    
    def __init__(
        self,
        redis_client: RedisClient,
        postgres_client: PostgreSQLClient,
        sync_interval: int = 300  # 5 minutes
    ):
        self.redis = redis_client
        self.postgres = postgres_client
        self.sync_interval = sync_interval
        self._sync_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    async def start(self) -> None:
        """Start the memory bus and sync task"""
        if self._sync_task is None:
            self._sync_task = asyncio.create_task(self._sync_loop())
    
    async def stop(self) -> None:
        """Stop the memory bus"""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
    
    async def store_memory(self, memory: MemoryStream) -> str:
        """Store a memory stream entry"""
        async with self._lock:
            # Store in Redis first (fast access)
            await self._store_in_redis(memory)
            
            # Store in PostgreSQL based on retention policy
            if memory.retention_policy in [RetentionPolicy.ARCHIVED, RetentionPolicy.PERMANENT]:
                await self._store_in_postgres(memory)
            
            return str(memory.id)
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryStream]:
        """Get a memory stream entry by ID"""
        # Try Redis first
        memory = await self._get_from_redis(memory_id)
        if memory:
            return memory
        
        # Fallback to PostgreSQL
        memory = await self._get_from_postgres(memory_id)
        if memory:
            # Restore to Redis for future fast access
            await self._store_in_redis(memory)
        
        return memory
    
    async def query_memories(self, query: MemoryQuery) -> List[MemoryStream]:
        """Query memory streams"""
        # For complex queries, use PostgreSQL
        if query.stream_ids or query.actors or query.time_range or query.confidence_threshold:
            return await self._query_from_postgres(query)
        
        # For simple queries, try Redis first
        memories = await self._query_from_redis(query)
        if not memories:
            memories = await self._query_from_postgres(query)
        
        return memories
    
    async def get_stream_memories(
        self,
        stream_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[MemoryStream]:
        """Get memories for a specific stream"""
        # Use Redis Streams for real-time access
        stream_key = f"memory_stream:{stream_id}"
        entries = await self.redis.xrange(stream_key, count=limit)
        
        memories = []
        for entry_id, fields in entries:
            memory = MemoryStream.from_redis_stream_entry(dict(fields))
            memories.append(memory)
        
        return memories
    
    async def subscribe_to_stream(
        self,
        stream_id: str,
        callback: callable
    ) -> None:
        """Subscribe to a memory stream for real-time updates"""
        stream_key = f"memory_stream:{stream_id}"
        
        # Start from the end of the stream
        last_id = "$"
        
        while True:
            try:
                # Read new entries
                result = await self.redis.xread({stream_key: last_id}, block=1000)
                
                if result:
                    for stream, entries in result:
                        for entry_id, fields in entries:
                            memory = MemoryStream.from_redis_stream_entry(dict(fields))
                            await callback(memory)
                            last_id = entry_id
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Stream subscription error: {e}")
                await asyncio.sleep(1)
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory bus statistics"""
        # Redis stats
        redis_keys = await self.redis.keys("memory_stream:*")
        redis_count = len(redis_keys)
        
        # PostgreSQL stats
        postgres_count = await self.postgres.fetchval(
            "SELECT COUNT(*) FROM uap.memory_streams"
        )
        
        # Stream stats
        stream_keys = await self.redis.keys("memory_stream:*")
        stream_count = len(stream_keys)
        
        return {
            "redis_memories": redis_count,
            "postgres_memories": postgres_count,
            "active_streams": stream_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup_expired_memories(self) -> int:
        """Clean up expired memories based on retention policies"""
        cleaned_count = 0
        
        # Clean up ephemeral memories from Redis
        redis_keys = await self.redis.keys("memory_stream:*")
        for key in redis_keys:
            ttl = await self.redis.ttl(key)
            if ttl == -1:  # No expiration set
                # Check if it's an ephemeral memory
                memory_data = await self.redis.hgetall(key)
                if memory_data.get("retention_policy") == RetentionPolicy.EPHEMERAL.value:
                    # Set TTL for ephemeral memories (24 hours)
                    await self.redis.expire(key, 86400)
            elif ttl == -2:  # Key doesn't exist
                cleaned_count += 1
        
        # Clean up archived memories (move from Redis to PostgreSQL)
        archived_keys = []
        for key in redis_keys:
            memory_data = await self.redis.hgetall(key)
            if memory_data.get("retention_policy") == RetentionPolicy.ARCHIVED.value:
                archived_keys.append(key)
        
        for key in archived_keys:
            memory_data = await self.redis.hgetall(key)
            memory = MemoryStream.from_redis_stream_entry(memory_data)
            
            # Store in PostgreSQL
            await self._store_in_postgres(memory)
            
            # Remove from Redis
            await self.redis.delete(key)
            cleaned_count += 1
        
        return cleaned_count
    
    async def _store_in_redis(self, memory: MemoryStream) -> None:
        """Store memory in Redis"""
        key = f"memory_stream:{memory.id}"
        data = memory.to_redis_stream_entry()
        
        await self.redis.hset(key, data)
        
        # Add to stream
        stream_key = f"memory_stream:{memory.stream_id}"
        await self.redis.xadd(stream_key, data)
        
        # Set TTL based on retention policy
        if memory.retention_policy == RetentionPolicy.EPHEMERAL:
            await self.redis.expire(key, 86400)  # 24 hours
        elif memory.retention_policy == RetentionPolicy.ARCHIVED:
            await self.redis.expire(key, 3600)  # 1 hour (will be moved to PostgreSQL)
        # PERMANENT memories don't have TTL
    
    async def _store_in_postgres(self, memory: MemoryStream) -> None:
        """Store memory in PostgreSQL"""
        await self.postgres.create_memory_stream(
            stream_id=memory.stream_id,
            actor=memory.actor,
            intent=memory.intent,
            context=memory.context,
            result=memory.result,
            confidence=memory.confidence,
            next_action=memory.next_action,
            granularity=memory.granularity.value,
            retention_policy=memory.retention_policy.value
        )
    
    async def _get_from_redis(self, memory_id: str) -> Optional[MemoryStream]:
        """Get memory from Redis"""
        key = f"memory_stream:{memory_id}"
        data = await self.redis.hgetall(key)
        
        if not data:
            return None
        
        return MemoryStream.from_redis_stream_entry(data)
    
    async def _get_from_postgres(self, memory_id: str) -> Optional[MemoryStream]:
        """Get memory from PostgreSQL"""
        query = """
        SELECT stream_id, actor, intent, context, result, confidence,
               next_action, granularity, retention_policy, created_at
        FROM uap.memory_streams
        WHERE id = $1
        """
        
        row = await self.postgres.fetchrow(query, memory_id)
        if not row:
            return None
        
        return MemoryStream(
            id=UUID(memory_id),
            stream_id=row["stream_id"],
            actor=row["actor"],
            intent=json.loads(row["intent"]),
            context=json.loads(row["context"]) if row["context"] else None,
            result=json.loads(row["result"]) if row["result"] else None,
            confidence=row["confidence"],
            next_action=row["next_action"],
            granularity=MemoryGranularity(row["granularity"]),
            retention_policy=RetentionPolicy(row["retention_policy"]),
            created_at=row["created_at"]
        )
    
    async def _query_from_redis(self, query: MemoryQuery) -> List[MemoryStream]:
        """Query memories from Redis"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated querying
        memories = []
        
        # Get all memory keys
        keys = await self.redis.keys("memory_stream:*")
        
        for key in keys:
            memory_data = await self.redis.hgetall(key)
            if memory_data:
                memory = MemoryStream.from_redis_stream_entry(memory_data)
                
                # Apply filters
                if self._matches_query(memory, query):
                    memories.append(memory)
        
        # Apply limit and offset
        return memories[query.offset:query.offset + query.limit]
    
    async def _query_from_postgres(self, query: MemoryQuery) -> List[MemoryStream]:
        """Query memories from PostgreSQL"""
        where_clause, params = query.to_sql_where_clause()
        
        sql_query = f"""
        SELECT id, stream_id, actor, intent, context, result, confidence,
               next_action, granularity, retention_policy, created_at
        FROM uap.memory_streams
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        params.extend([query.limit, query.offset])
        
        rows = await self.postgres.fetch(sql_query, *params)
        
        memories = []
        for row in rows:
            memories.append(MemoryStream(
                id=UUID(row["id"]),
                stream_id=row["stream_id"],
                actor=row["actor"],
                intent=json.loads(row["intent"]),
                context=json.loads(row["context"]) if row["context"] else None,
                result=json.loads(row["result"]) if row["result"] else None,
                confidence=row["confidence"],
                next_action=row["next_action"],
                granularity=MemoryGranularity(row["granularity"]),
                retention_policy=RetentionPolicy(row["retention_policy"]),
                created_at=row["created_at"]
            ))
        
        return memories
    
    def _matches_query(self, memory: MemoryStream, query: MemoryQuery) -> bool:
        """Check if a memory matches a query"""
        # Check granularity
        if query.granularity and memory.granularity not in query.granularity:
            return False
        
        # Check retention policy
        if query.retention_policy and memory.retention_policy not in query.retention_policy:
            return False
        
        # Check confidence threshold
        if query.confidence_threshold and memory.confidence is not None:
            if memory.confidence < query.confidence_threshold:
                return False
        
        # Check actors
        if query.actors and memory.actor not in query.actors:
            return False
        
        # Check stream IDs (with wildcard support)
        if query.stream_ids:
            matches = False
            for pattern in query.stream_ids:
                if "*" in pattern:
                    import fnmatch
                    if fnmatch.fnmatch(memory.stream_id, pattern):
                        matches = True
                        break
                elif memory.stream_id == pattern:
                    matches = True
                    break
            if not matches:
                return False
        
        return True
    
    async def _sync_loop(self) -> None:
        """Background sync loop"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                await self.cleanup_expired_memories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Memory bus sync error: {e}")
