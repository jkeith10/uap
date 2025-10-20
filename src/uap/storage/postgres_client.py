"""PostgreSQL Client for UAP"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timezone

import asyncpg
from asyncpg import Connection, Pool
from pydantic import BaseModel, Field


class PostgreSQLConfig(BaseModel):
    """PostgreSQL configuration"""
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    database: str = Field(default="uap", description="Database name")
    user: str = Field(default="uap", description="Database user")
    password: str = Field(default="uap_password", description="Database password")
    min_size: int = Field(default=5, description="Minimum number of connections")
    max_size: int = Field(default=20, description="Maximum number of connections")
    command_timeout: int = Field(default=60, description="Command timeout in seconds")
    server_settings: Dict[str, str] = Field(default_factory=dict, description="Server settings")


class PostgreSQLClient:
    """Async PostgreSQL client for UAP"""
    
    def __init__(self, config: PostgreSQLConfig):
        self.config = config
        self._pool: Optional[Pool] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect to PostgreSQL"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                command_timeout=self.config.command_timeout,
                server_settings=self.config.server_settings
            )
    
    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL"""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results"""
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows"""
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row"""
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value"""
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def transaction(self):
        """Get a transaction context manager"""
        return self._pool.acquire()
    
    # World State operations
    async def set_world_state(
        self,
        key: str,
        value: Any,
        version: int = 1
    ) -> None:
        """Set a world state entry"""
        query = """
        INSERT INTO uap.world_state (key, value, version, created_at, updated_at)
        VALUES ($1, $2, $3, NOW(), NOW())
        ON CONFLICT (key) DO UPDATE SET
            value = EXCLUDED.value,
            version = EXCLUDED.version,
            updated_at = NOW()
        """
        await self.execute(query, key, json.dumps(value, default=str), version)
    
    async def get_world_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a world state entry"""
        query = "SELECT value, version, created_at, updated_at FROM uap.world_state WHERE key = $1"
        row = await self.fetchrow(query, key)
        
        if row:
            return {
                "value": json.loads(row["value"]),
                "version": row["version"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None
    
    async def delete_world_state(self, key: str) -> bool:
        """Delete a world state entry"""
        query = "DELETE FROM uap.world_state WHERE key = $1"
        result = await self.execute(query, key)
        return result == "DELETE 1"
    
    # Memory Stream operations
    async def create_memory_stream(
        self,
        stream_id: str,
        actor: str,
        intent: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        next_action: Optional[str] = None,
        granularity: str = "task",
        retention_policy: str = "permanent"
    ) -> str:
        """Create a memory stream entry"""
        query = """
        INSERT INTO uap.memory_streams (
            stream_id, actor, intent, context, result, confidence, 
            next_action, granularity, retention_policy, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
        RETURNING id
        """
        
        result_id = await self.fetchval(
            query,
            stream_id,
            actor,
            json.dumps(intent),
            json.dumps(context) if context else None,
            json.dumps(result) if result else None,
            confidence,
            next_action,
            granularity,
            retention_policy
        )
        
        return str(result_id)
    
    async def get_memory_streams(
        self,
        stream_id: Optional[str] = None,
        actor: Optional[str] = None,
        granularity: Optional[str] = None,
        retention_policy: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get memory stream entries"""
        conditions = []
        params = []
        param_count = 0
        
        if stream_id:
            param_count += 1
            conditions.append(f"stream_id = ${param_count}")
            params.append(stream_id)
        
        if actor:
            param_count += 1
            conditions.append(f"actor = ${param_count}")
            params.append(actor)
        
        if granularity:
            param_count += 1
            conditions.append(f"granularity = ${param_count}")
            params.append(granularity)
        
        if retention_policy:
            param_count += 1
            conditions.append(f"retention_policy = ${param_count}")
            params.append(retention_policy)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
        SELECT id, stream_id, actor, intent, context, result, confidence,
               next_action, granularity, retention_policy, created_at
        FROM uap.memory_streams
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])
        
        rows = await self.fetch(query, *params)
        
        results = []
        for row in rows:
            results.append({
                "id": str(row["id"]),
                "stream_id": row["stream_id"],
                "actor": row["actor"],
                "intent": json.loads(row["intent"]),
                "context": json.loads(row["context"]) if row["context"] else None,
                "result": json.loads(row["result"]) if row["result"] else None,
                "confidence": row["confidence"],
                "next_action": row["next_action"],
                "granularity": row["granularity"],
                "retention_policy": row["retention_policy"],
                "created_at": row["created_at"]
            })
        
        return results
    
    # Action Graph operations
    async def create_action_graph(
        self,
        graph_id: str,
        name: str,
        definition: Dict[str, Any],
        status: str = "draft"
    ) -> str:
        """Create an action graph"""
        query = """
        INSERT INTO uap.action_graphs (graph_id, name, definition, status, created_at, updated_at)
        VALUES ($1, $2, $3, $4, NOW(), NOW())
        RETURNING id
        """
        
        result_id = await self.fetchval(
            query,
            graph_id,
            name,
            json.dumps(definition),
            status
        )
        
        return str(result_id)
    
    async def get_action_graph(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get an action graph"""
        query = "SELECT id, graph_id, name, definition, status, created_at, updated_at FROM uap.action_graphs WHERE graph_id = $1"
        row = await self.fetchrow(query, graph_id)
        
        if row:
            return {
                "id": str(row["id"]),
                "graph_id": row["graph_id"],
                "name": row["name"],
                "definition": json.loads(row["definition"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None
    
    async def update_action_graph_status(self, graph_id: str, status: str) -> bool:
        """Update action graph status"""
        query = "UPDATE uap.action_graphs SET status = $1, updated_at = NOW() WHERE graph_id = $2"
        result = await self.execute(query, status, graph_id)
        return result == "UPDATE 1"
    
    # Node Capabilities operations
    async def register_node_capability(
        self,
        node_id: str,
        name: str,
        capabilities: Dict[str, Any],
        fingerprint: Dict[str, Any],
        cost_weight: float = 1.0,
        latency_weight: float = 1.0,
        confidence_weight: float = 1.0
    ) -> str:
        """Register a node capability"""
        query = """
        INSERT INTO uap.node_capabilities (
            node_id, name, capabilities, fingerprint, cost_weight,
            latency_weight, confidence_weight, is_active, created_at, updated_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, true, NOW(), NOW())
        ON CONFLICT (node_id) DO UPDATE SET
            name = EXCLUDED.name,
            capabilities = EXCLUDED.capabilities,
            fingerprint = EXCLUDED.fingerprint,
            cost_weight = EXCLUDED.cost_weight,
            latency_weight = EXCLUDED.latency_weight,
            confidence_weight = EXCLUDED.confidence_weight,
            updated_at = NOW()
        RETURNING id
        """
        
        result_id = await self.fetchval(
            query,
            node_id,
            name,
            json.dumps(capabilities),
            json.dumps(fingerprint),
            cost_weight,
            latency_weight,
            confidence_weight
        )
        
        return str(result_id)
    
    async def get_node_capabilities(self, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get node capabilities"""
        if node_id:
            query = "SELECT * FROM uap.node_capabilities WHERE node_id = $1"
            rows = await self.fetch(query, node_id)
        else:
            query = "SELECT * FROM uap.node_capabilities WHERE is_active = true ORDER BY updated_at DESC"
            rows = await self.fetch(query)
        
        results = []
        for row in rows:
            results.append({
                "id": str(row["id"]),
                "node_id": row["node_id"],
                "name": row["name"],
                "capabilities": json.loads(row["capabilities"]),
                "fingerprint": json.loads(row["fingerprint"]),
                "cost_weight": row["cost_weight"],
                "latency_weight": row["latency_weight"],
                "confidence_weight": row["confidence_weight"],
                "performance_history": json.loads(row["performance_history"]),
                "is_active": row["is_active"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return results
    
    # Reflection Report operations
    async def create_reflection_report(
        self,
        report_id: str,
        actor: str,
        intent: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        next_action: Optional[str] = None,
        evaluation: Dict[str, Any] = None,
        recommendations: Dict[str, Any] = None
    ) -> str:
        """Create a reflection report"""
        query = """
        INSERT INTO uap.reflection_reports (
            report_id, actor, intent, context, result, confidence,
            next_action, evaluation, recommendations, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
        RETURNING id
        """
        
        result_id = await self.fetchval(
            query,
            report_id,
            actor,
            json.dumps(intent),
            json.dumps(context) if context else None,
            json.dumps(result) if result else None,
            confidence,
            next_action,
            json.dumps(evaluation) if evaluation else None,
            json.dumps(recommendations) if recommendations else None
        )
        
        return str(result_id)
    
    async def get_reflection_reports(
        self,
        actor: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get reflection reports"""
        if actor:
            query = """
            SELECT * FROM uap.reflection_reports 
            WHERE actor = $1 
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """
            rows = await self.fetch(query, actor, limit, offset)
        else:
            query = """
            SELECT * FROM uap.reflection_reports 
            ORDER BY created_at DESC 
            LIMIT $1 OFFSET $2
            """
            rows = await self.fetch(query, limit, offset)
        
        results = []
        for row in rows:
            results.append({
                "id": str(row["id"]),
                "report_id": row["report_id"],
                "actor": row["actor"],
                "intent": json.loads(row["intent"]),
                "context": json.loads(row["context"]) if row["context"] else None,
                "result": json.loads(row["result"]) if row["result"] else None,
                "confidence": row["confidence"],
                "next_action": row["next_action"],
                "evaluation": json.loads(row["evaluation"]) if row["evaluation"] else None,
                "recommendations": json.loads(row["recommendations"]) if row["recommendations"] else None,
                "created_at": row["created_at"]
            })
        
        return results
    
    # Vector similarity search (requires pgvector extension)
    async def vector_search(
        self,
        table: str,
        vector_column: str,
        query_vector: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        query = f"""
        SELECT *, {vector_column} <-> $1::vector AS distance
        FROM {table}
        WHERE {vector_column} <-> $1::vector < $2
        ORDER BY {vector_column} <-> $1::vector
        LIMIT $3
        """
        
        rows = await self.fetch(query, query_vector, similarity_threshold, limit)
        
        results = []
        for row in rows:
            result = dict(row)
            result["distance"] = float(result["distance"])
            results.append(result)
        
        return results
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check"""
        try:
            start_time = datetime.now(timezone.utc)
            await self.fetchval("SELECT 1")
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
