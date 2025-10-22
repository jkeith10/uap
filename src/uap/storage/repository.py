"""Repository layer for UAP data models"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone

from ..models.intent import IntentPacket
from ..models.action_graph import ActionGraph
from ..models.memory_stream import MemoryStream
from ..models.reflection import ReflectionReport
from ..logging_config import get_logger
from ..exceptions import StorageError
from .postgres_client import PostgreSQLClient

logger = get_logger(__name__)


class IntentRepository:
    """Repository for Intent operations"""
    
    def __init__(self, db: PostgreSQLClient):
        self.db = db
    
    async def create(self, intent: IntentPacket) -> IntentPacket:
        """Create a new intent"""
        try:
            query = """
                INSERT INTO intents (id, type, content, context, priority, created_at, updated_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """
            await self.db.execute(
                query,
                intent.id,
                intent.type.value,
                intent.content,
                intent.context,
                intent.priority.value,
                intent.created_at,
                intent.created_at,
                {}
            )
            logger.info("Intent created", intent_id=str(intent.id))
            return intent
        except Exception as e:
            logger.error("Failed to create intent", error=str(e), exc_info=True)
            raise StorageError(f"Failed to create intent: {e}")
    
    async def get(self, intent_id: UUID) -> Optional[IntentPacket]:
        """Get intent by ID"""
        try:
            query = "SELECT * FROM intents WHERE id = $1"
            row = await self.db.fetchrow(query, intent_id)
            if not row:
                return None
            return IntentPacket(**dict(row))
        except Exception as e:
            logger.error("Failed to get intent", error=str(e), exc_info=True)
            raise StorageError(f"Failed to get intent: {e}")
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[IntentPacket]:
        """List intents with pagination"""
        try:
            query = "SELECT * FROM intents ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            rows = await self.db.fetch(query, limit, offset)
            return [IntentPacket(**dict(row)) for row in rows]
        except Exception as e:
            logger.error("Failed to list intents", error=str(e), exc_info=True)
            raise StorageError(f"Failed to list intents: {e}")
    
    async def update(self, intent_id: UUID, updates: Dict[str, Any]) -> Optional[IntentPacket]:
        """Update intent"""
        try:
            set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
            query = f"UPDATE intents SET {set_clause}, updated_at = $1 WHERE id = ${len(updates)+2} RETURNING *"
            values = [datetime.now(timezone.utc)] + list(updates.values()) + [intent_id]
            row = await self.db.fetchrow(query, *values)
            if not row:
                return None
            return IntentPacket(**dict(row))
        except Exception as e:
            logger.error("Failed to update intent", error=str(e), exc_info=True)
            raise StorageError(f"Failed to update intent: {e}")
    
    async def delete(self, intent_id: UUID) -> bool:
        """Delete intent"""
        try:
            query = "DELETE FROM intents WHERE id = $1"
            result = await self.db.execute(query, intent_id)
            return True
        except Exception as e:
            logger.error("Failed to delete intent", error=str(e), exc_info=True)
            raise StorageError(f"Failed to delete intent: {e}")


class ActionGraphRepository:
    """Repository for ActionGraph operations"""
    
    def __init__(self, db: PostgreSQLClient):
        self.db = db
    
    async def create(self, graph: ActionGraph) -> ActionGraph:
        """Create a new action graph"""
        try:
            query = """
                INSERT INTO action_graphs (id, status, nodes, edges, created_at, updated_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """
            await self.db.execute(
                query,
                graph.id,
                graph.status.value,
                [node.model_dump() for node in graph.nodes],
                graph.edges,
                graph.created_at,
                graph.updated_at,
                {}
            )
            logger.info("Action graph created", graph_id=str(graph.id))
            return graph
        except Exception as e:
            logger.error("Failed to create action graph", error=str(e), exc_info=True)
            raise StorageError(f"Failed to create action graph: {e}")
    
    async def get(self, graph_id: UUID) -> Optional[ActionGraph]:
        """Get action graph by ID"""
        try:
            query = "SELECT * FROM action_graphs WHERE id = $1"
            row = await self.db.fetchrow(query, graph_id)
            if not row:
                return None
            return ActionGraph(**dict(row))
        except Exception as e:
            logger.error("Failed to get action graph", error=str(e), exc_info=True)
            raise StorageError(f"Failed to get action graph: {e}")
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[ActionGraph]:
        """List action graphs with pagination"""
        try:
            query = "SELECT * FROM action_graphs ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            rows = await self.db.fetch(query, limit, offset)
            return [ActionGraph(**dict(row)) for row in rows]
        except Exception as e:
            logger.error("Failed to list action graphs", error=str(e), exc_info=True)
            raise StorageError(f"Failed to list action graphs: {e}")
    
    async def update(self, graph_id: UUID, updates: Dict[str, Any]) -> Optional[ActionGraph]:
        """Update action graph"""
        try:
            set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
            query = f"UPDATE action_graphs SET {set_clause}, updated_at = $1 WHERE id = ${len(updates)+2} RETURNING *"
            values = [datetime.now(timezone.utc)] + list(updates.values()) + [graph_id]
            row = await self.db.fetchrow(query, *values)
            if not row:
                return None
            return ActionGraph(**dict(row))
        except Exception as e:
            logger.error("Failed to update action graph", error=str(e), exc_info=True)
            raise StorageError(f"Failed to update action graph: {e}")


class MemoryRepository:
    """Repository for MemoryStream operations with vector search"""
    
    def __init__(self, db: PostgreSQLClient):
        self.db = db
    
    async def create(self, memory: MemoryStream, vector_embedding: Optional[List[float]] = None) -> MemoryStream:
        """Create a new memory stream"""
        try:
            query = """
                INSERT INTO memory_streams (id, granularity, entries, vector_embedding, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """
            await self.db.execute(
                query,
                memory.id,
                memory.granularity.value,
                [entry.model_dump() for entry in memory.entries],
                vector_embedding,
                memory.created_at,
                {}
            )
            logger.info("Memory stream created", memory_id=str(memory.id))
            return memory
        except Exception as e:
            logger.error("Failed to create memory stream", error=str(e), exc_info=True)
            raise StorageError(f"Failed to create memory stream: {e}")
    
    async def get(self, memory_id: UUID) -> Optional[MemoryStream]:
        """Get memory stream by ID"""
        try:
            query = "SELECT * FROM memory_streams WHERE id = $1"
            row = await self.db.fetchrow(query, memory_id)
            if not row:
                return None
            return MemoryStream(**dict(row))
        except Exception as e:
            logger.error("Failed to get memory stream", error=str(e), exc_info=True)
            raise StorageError(f"Failed to get memory stream: {e}")
    
    async def search_similar(self, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar memories using vector similarity"""
        try:
            query = """
                SELECT id, granularity, entries, created_at,
                       1 - (vector_embedding <=> $1::vector) AS similarity
                FROM memory_streams
                WHERE vector_embedding IS NOT NULL
                ORDER BY vector_embedding <=> $1::vector
                LIMIT $2
            """
            rows = await self.db.fetch(query, query_vector, limit)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Failed to search memories", error=str(e), exc_info=True)
            raise StorageError(f"Failed to search memories: {e}")
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[MemoryStream]:
        """List memory streams with pagination"""
        try:
            query = "SELECT * FROM memory_streams ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            rows = await self.db.fetch(query, limit, offset)
            return [MemoryStream(**dict(row)) for row in rows]
        except Exception as e:
            logger.error("Failed to list memory streams", error=str(e), exc_info=True)
            raise StorageError(f"Failed to list memory streams: {e}")


class ReflectionRepository:
    """Repository for ReflectionReport operations"""
    
    def __init__(self, db: PostgreSQLClient):
        self.db = db
    
    async def create(self, report: ReflectionReport) -> ReflectionReport:
        """Create a new reflection report"""
        try:
            query = """
                INSERT INTO reflection_reports (id, type, evaluations, score, feedback, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """
            # Calculate average score from evaluations
            scores = [eval.score for eval in report.evaluations if hasattr(eval, 'score')]
            avg_score = sum(scores) / len(scores) if scores else None
            
            await self.db.execute(
                query,
                report.id,
                report.type,
                [eval.model_dump() for eval in report.evaluations],
                avg_score,
                {},
                report.created_at,
                {}
            )
            logger.info("Reflection report created", report_id=str(report.id))
            return report
        except Exception as e:
            logger.error("Failed to create reflection report", error=str(e), exc_info=True)
            raise StorageError(f"Failed to create reflection report: {e}")
    
    async def get(self, report_id: UUID) -> Optional[ReflectionReport]:
        """Get reflection report by ID"""
        try:
            query = "SELECT * FROM reflection_reports WHERE id = $1"
            row = await self.db.fetchrow(query, report_id)
            if not row:
                return None
            return ReflectionReport(**dict(row))
        except Exception as e:
            logger.error("Failed to get reflection report", error=str(e), exc_info=True)
            raise StorageError(f"Failed to get reflection report: {e}")
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[ReflectionReport]:
        """List reflection reports with pagination"""
        try:
            query = "SELECT * FROM reflection_reports ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            rows = await self.db.fetch(query, limit, offset)
            return [ReflectionReport(**dict(row)) for row in rows]
        except Exception as e:
            logger.error("Failed to list reflection reports", error=str(e), exc_info=True)
            raise StorageError(f"Failed to list reflection reports: {e}")


