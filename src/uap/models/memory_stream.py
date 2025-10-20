"""Memory Stream Models"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict


class MemoryGranularity(str, Enum):
    """Granularity levels for memory streams"""
    TASK = "task"
    AGENT = "agent"
    ORGANIZATION = "organization"


class RetentionPolicy(str, Enum):
    """Retention policies for memory streams"""
    EPHEMERAL = "ephemeral"  # Stored in Redis only, TTL-based
    ARCHIVED = "archived"    # Moved to PostgreSQL after TTL
    PERMANENT = "permanent"  # Stored in PostgreSQL permanently


class MemoryStream(BaseModel):
    """Memory stream entry for cross-session sharing"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "stream_id": "BellOps/pricebook/changeset",
                "actor": "Agent:BellOps.Worker",
                "intent": {
                    "type": "optimize",
                    "goal": "Update HVAC pricebook"
                },
                "context": {
                    "pricebook": "v3.1",
                    "domain": "hvac"
                },
                "result": {
                    "margin": "+8%",
                    "status": "success"
                },
                "confidence": 0.91,
                "next_action": "Audit",
                "granularity": "task",
                "retention_policy": "permanent",
                "created_at": "2024-01-01T10:00:00Z"
            }
        }
    )
    
    id: UUID = Field(default_factory=uuid4, description="Unique memory entry identifier")
    stream_id: str = Field(description="Stream identifier (e.g., 'BellOps/pricebook/changeset')")
    actor: str = Field(description="Actor that created this memory (e.g., 'Agent:BellOps.Worker')")
    intent: Dict[str, Any] = Field(description="Intent that led to this memory")
    context: Optional[Dict[str, Any]] = Field(None, description="Contextual information")
    result: Optional[Dict[str, Any]] = Field(None, description="Result of the action")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    next_action: Optional[str] = Field(None, description="Suggested next action")
    granularity: MemoryGranularity = Field(description="Memory granularity level")
    retention_policy: RetentionPolicy = Field(description="Retention policy for this memory")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    
    def to_redis_stream_entry(self) -> Dict[str, str]:
        """Convert to Redis Stream entry format"""
        return {
            "id": str(self.id),
            "stream_id": self.stream_id,
            "actor": self.actor,
            "intent": str(self.intent),
            "context": str(self.context) if self.context else "",
            "result": str(self.result) if self.result else "",
            "confidence": str(self.confidence) if self.confidence else "",
            "next_action": self.next_action or "",
            "granularity": self.granularity.value,
            "retention_policy": self.retention_policy.value,
            "metadata": str(self.metadata),
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_redis_stream_entry(cls, entry_data: Dict[str, str]) -> "MemoryStream":
        """Create from Redis Stream entry format"""
        import json
        
        return cls(
            id=UUID(entry_data["id"]),
            stream_id=entry_data["stream_id"],
            actor=entry_data["actor"],
            intent=json.loads(entry_data["intent"]) if entry_data["intent"] else {},
            context=json.loads(entry_data["context"]) if entry_data["context"] else None,
            result=json.loads(entry_data["result"]) if entry_data["result"] else None,
            confidence=float(entry_data["confidence"]) if entry_data["confidence"] else None,
            next_action=entry_data["next_action"] if entry_data["next_action"] else None,
            granularity=MemoryGranularity(entry_data["granularity"]),
            retention_policy=RetentionPolicy(entry_data["retention_policy"]),
            metadata=json.loads(entry_data["metadata"]) if entry_data["metadata"] else {},
            created_at=datetime.fromisoformat(entry_data["created_at"])
        )
    
    def to_json_ld(self) -> Dict[str, Any]:
        """Convert to JSON-LD format for semantic interoperability"""
        return {
            "@context": {
                "@vocab": "https://uap.dev/schema#",
                "uap": "https://uap.dev/schema#"
            },
            "@type": "uap:MemoryStream",
            "@id": str(self.id),
            "uap:streamId": self.stream_id,
            "uap:actor": self.actor,
            "uap:intent": self.intent,
            "uap:context": self.context,
            "uap:result": self.result,
            "uap:confidence": self.confidence,
            "uap:nextAction": self.next_action,
            "uap:granularity": self.granularity.value,
            "uap:retentionPolicy": self.retention_policy.value,
            "uap:metadata": self.metadata,
            "uap:createdAt": self.created_at.isoformat()
        }
    
    @classmethod
    def from_json_ld(cls, data: Dict[str, Any]) -> "MemoryStream":
        """Create from JSON-LD format"""
        return cls(
            id=UUID(data["@id"]),
            stream_id=data["uap:streamId"],
            actor=data["uap:actor"],
            intent=data["uap:intent"],
            context=data.get("uap:context"),
            result=data.get("uap:result"),
            confidence=data.get("uap:confidence"),
            next_action=data.get("uap:nextAction"),
            granularity=MemoryGranularity(data["uap:granularity"]),
            retention_policy=RetentionPolicy(data["uap:retentionPolicy"]),
            metadata=data.get("uap:metadata", {}),
            created_at=datetime.fromisoformat(data["uap:createdAt"])
        )


class MemoryQuery(BaseModel):
    """Query structure for memory streams"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stream_ids": ["BellOps/pricebook/*"],
                "actors": ["Agent:BellOps.Worker"],
                "granularity": ["task", "agent"],
                "retention_policy": ["permanent"],
                "time_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-31T23:59:59Z"
                },
                "confidence_threshold": 0.8,
                "limit": 100
            }
        }
    )
    
    stream_ids: Optional[List[str]] = Field(None, description="Stream ID patterns to match")
    actors: Optional[List[str]] = Field(None, description="Actors to filter by")
    granularity: Optional[List[MemoryGranularity]] = Field(None, description="Granularity levels to include")
    retention_policy: Optional[List[RetentionPolicy]] = Field(None, description="Retention policies to include")
    time_range: Optional[Dict[str, datetime]] = Field(None, description="Time range filter")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence score")
    intent_filters: Optional[Dict[str, Any]] = Field(None, description="Intent-based filters")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    
    def to_sql_where_clause(self) -> tuple[str, Dict[str, Any]]:
        """Convert to SQL WHERE clause and parameters"""
        conditions = []
        params = {}
        
        if self.stream_ids:
            # Handle wildcard patterns
            stream_conditions = []
            for i, stream_id in enumerate(self.stream_ids):
                if "*" in stream_id:
                    # Convert wildcard to SQL LIKE pattern
                    pattern = stream_id.replace("*", "%")
                    stream_conditions.append(f"stream_id LIKE :stream_pattern_{i}")
                    params[f"stream_pattern_{i}"] = pattern
                else:
                    stream_conditions.append(f"stream_id = :stream_exact_{i}")
                    params[f"stream_exact_{i}"] = stream_id
            
            if stream_conditions:
                conditions.append(f"({' OR '.join(stream_conditions)})")
        
        if self.actors:
            actor_conditions = []
            for i, actor in enumerate(self.actors):
                actor_conditions.append(f"actor = :actor_{i}")
                params[f"actor_{i}"] = actor
            conditions.append(f"({' OR '.join(actor_conditions)})")
        
        if self.granularity:
            granularity_values = [g.value for g in self.granularity]
            conditions.append("granularity = ANY(:granularity)")
            params["granularity"] = granularity_values
        
        if self.retention_policy:
            retention_values = [r.value for r in self.retention_policy]
            conditions.append("retention_policy = ANY(:retention_policy)")
            params["retention_policy"] = retention_values
        
        if self.time_range:
            if "start" in self.time_range:
                conditions.append("created_at >= :time_start")
                params["time_start"] = self.time_range["start"]
            if "end" in self.time_range:
                conditions.append("created_at <= :time_end")
                params["time_end"] = self.time_range["end"]
        
        if self.confidence_threshold is not None:
            conditions.append("confidence >= :confidence_threshold")
            params["confidence_threshold"] = self.confidence_threshold
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params
