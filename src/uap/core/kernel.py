"""World State Manager - Core of the Contextual Kernel"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from ..storage.redis_client import RedisClient
from ..storage.postgres_client import PostgreSQLClient
from .versioning import SemanticVersion
from ..logging_config import core_logger


@dataclass
class WorldStateEntry:
    """Entry in the world state"""
    key: str
    value: Any
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Set[str] = field(default_factory=set)
    ttl: Optional[timedelta] = None


class WorldStateManager:
    """Manages persistent world state shared between all UAP nodes"""
    
    def __init__(
        self,
        redis_client: RedisClient,
        postgres_client: PostgreSQLClient,
        sync_interval: int = 60
    ):
        self.redis = redis_client
        self.postgres = postgres_client
        self.sync_interval = sync_interval
        self._sync_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start the world state manager and sync task"""
        if self._sync_task is None:
            self._sync_task = asyncio.create_task(self._sync_loop())
    
    async def stop(self) -> None:
        """Stop the world state manager"""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
    
    async def set_state(
        self,
        key: str,
        value: Any,
        tags: Optional[Set[str]] = None,
        ttl: Optional[timedelta] = None,
        force_version: Optional[int] = None
    ) -> WorldStateEntry:
        """Set a world state entry with optimistic locking"""
        async with self._lock:
            # Get current version for optimistic locking
            current_entry = await self.get_state(key)
            new_version = force_version or (current_entry.version + 1 if current_entry else 1)
            
            entry = WorldStateEntry(
                key=key,
                value=value,
                version=new_version,
                tags=tags or set(),
                ttl=ttl
            )
            
            # Store in Redis first (fast access)
            await self._store_in_redis(entry)
            
            # Store in PostgreSQL for durability
            await self._store_in_postgres(entry)
            
            return entry
    
    async def get_state(self, key: str) -> Optional[WorldStateEntry]:
        """Get a world state entry"""
        # Try Redis first (fast access)
        entry = await self._get_from_redis(key)
        if entry:
            return entry
        
        # Fallback to PostgreSQL
        entry = await self._get_from_postgres(key)
        if entry:
            # Restore to Redis for future fast access
            await self._store_in_redis(entry)
        
        return entry
    
    async def update_state(
        self,
        key: str,
        updates: Dict[str, Any],
        expected_version: Optional[int] = None
    ) -> Optional[WorldStateEntry]:
        """Update a world state entry with optimistic locking"""
        async with self._lock:
            current_entry = await self.get_state(key)
            if not current_entry:
                return None
            
            # Check version for optimistic locking
            if expected_version is not None and current_entry.version != expected_version:
                raise ValueError(f"Version mismatch: expected {expected_version}, got {current_entry.version}")
            
            # Apply updates
            if isinstance(current_entry.value, dict):
                new_value = {**current_entry.value, **updates}
            else:
                new_value = updates
            
            # Create new entry with incremented version
            new_entry = WorldStateEntry(
                key=key,
                value=new_value,
                version=current_entry.version + 1,
                created_at=current_entry.created_at,
                tags=current_entry.tags,
                ttl=current_entry.ttl
            )
            
            # Store updated entry
            await self._store_in_redis(new_entry)
            await self._store_in_postgres(new_entry)
            
            return new_entry
    
    async def delete_state(self, key: str) -> bool:
        """Delete a world state entry"""
        async with self._lock:
            # Remove from both stores
            redis_deleted = await self._delete_from_redis(key)
            postgres_deleted = await self._delete_from_postgres(key)
            
            return redis_deleted or postgres_deleted
    
    async def query_state(
        self,
        pattern: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorldStateEntry]:
        """Query world state entries"""
        # For complex queries, use PostgreSQL
        if pattern or tags:
            return await self._query_from_postgres(pattern, tags, limit, offset)
        
        # For simple queries, try Redis first
        entries = await self._query_from_redis(limit, offset)
        if not entries:
            entries = await self._query_from_postgres(pattern, tags, limit, offset)
        
        return entries
    
    async def get_state_history(self, key: str, limit: int = 10) -> List[WorldStateEntry]:
        """Get version history for a state key"""
        return await self._get_history_from_postgres(key, limit)
    
    async def _store_in_redis(self, entry: WorldStateEntry) -> None:
        """Store entry in Redis"""
        data = {
            "value": json.dumps(entry.value, default=str),
            "version": entry.version,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "tags": json.dumps(list(entry.tags)),
            "ttl": entry.ttl.total_seconds() if entry.ttl else None
        }
        
        await self.redis.hset(f"world_state:{entry.key}", data)
        
        # Set TTL if specified
        if entry.ttl:
            await self.redis.expire(f"world_state:{entry.key}", int(entry.ttl.total_seconds()))
    
    async def _store_in_postgres(self, entry: WorldStateEntry) -> None:
        """Store entry in PostgreSQL"""
        query = """
        INSERT INTO uap.world_state (key, value, version, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (key) DO UPDATE SET
            value = EXCLUDED.value,
            version = EXCLUDED.version,
            updated_at = EXCLUDED.updated_at
        """
        
        await self.postgres.execute(
            query,
            entry.key,
            json.dumps(entry.value, default=str),
            entry.version,
            entry.created_at,
            entry.updated_at
        )
    
    async def _get_from_redis(self, key: str) -> Optional[WorldStateEntry]:
        """Get entry from Redis"""
        data = await self.redis.hgetall(f"world_state:{key}")
        if not data:
            return None
        
        return WorldStateEntry(
            key=key,
            value=json.loads(data["value"]),
            version=int(data["version"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tags=set(json.loads(data["tags"])),
            ttl=timedelta(seconds=float(data["ttl"])) if data.get("ttl") else None
        )
    
    async def _get_from_postgres(self, key: str) -> Optional[WorldStateEntry]:
        """Get entry from PostgreSQL"""
        query = "SELECT value, version, created_at, updated_at FROM uap.world_state WHERE key = $1"
        row = await self.postgres.fetchrow(query, key)
        
        if not row:
            return None
        
        return WorldStateEntry(
            key=key,
            value=json.loads(row["value"]),
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=set(),  # Tags not stored in PostgreSQL for now
            ttl=None
        )
    
    async def _delete_from_redis(self, key: str) -> bool:
        """Delete entry from Redis"""
        result = await self.redis.delete(f"world_state:{key}")
        return result > 0
    
    async def _delete_from_postgres(self, key: str) -> bool:
        """Delete entry from PostgreSQL"""
        query = "DELETE FROM uap.world_state WHERE key = $1"
        result = await self.postgres.execute(query, key)
        return result == "DELETE 1"
    
    async def _query_from_redis(self, limit: int, offset: int) -> List[WorldStateEntry]:
        """Query entries from Redis"""
        keys = await self.redis.keys("world_state:*")
        entries = []
        
        for key in keys[offset:offset + limit]:
            entry_key = key.decode().replace("world_state:", "")
            entry = await self._get_from_redis(entry_key)
            if entry:
                entries.append(entry)
        
        return entries
    
    async def _query_from_postgres(
        self,
        pattern: Optional[str],
        tags: Optional[Set[str]],
        limit: int,
        offset: int
    ) -> List[WorldStateEntry]:
        """Query entries from PostgreSQL"""
        conditions = []
        params = []
        param_count = 0
        
        if pattern:
            param_count += 1
            conditions.append(f"key LIKE ${param_count}")
            params.append(pattern)
        
        # Note: Tags filtering would require a separate tags table
        # For now, we'll skip tag filtering in PostgreSQL queries
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
        SELECT key, value, version, created_at, updated_at
        FROM uap.world_state
        WHERE {where_clause}
        ORDER BY updated_at DESC
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])
        
        rows = await self.postgres.fetch(query, *params)
        
        entries = []
        for row in rows:
            entries.append(WorldStateEntry(
                key=row["key"],
                value=json.loads(row["value"]),
                version=row["version"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                tags=set(),
                ttl=None
            ))
        
        return entries
    
    async def _get_history_from_postgres(self, key: str, limit: int) -> List[WorldStateEntry]:
        """Get version history from PostgreSQL"""
        # This would require a separate history table
        # For now, return current entry only
        entry = await self._get_from_postgres(key)
        return [entry] if entry else []
    
    async def _sync_loop(self) -> None:
        """Background sync loop between Redis and PostgreSQL"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                await self._sync_stores()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error and continue
                core_logger.error("Sync error", error=str(e), exc_info=True)
    
    async def _sync_stores(self) -> None:
        """Sync data between Redis and PostgreSQL"""
        # This is a simplified sync - in production, you'd want more sophisticated
        # conflict resolution and incremental sync
        pass
