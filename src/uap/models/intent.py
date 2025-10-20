"""Intent Packet Models"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict


class IntentType(str, Enum):
    """Types of intents that can be processed by UAP"""
    OPTIMIZE = "optimize"
    ANALYZE = "analyze"
    EXECUTE = "execute"
    COLLABORATE = "collaborate"
    REFLECT = "reflect"
    ROUTE = "route"
    MEMORIZE = "memorize"
    QUERY = "query"


class IntentPacket(BaseModel):
    """Core intent packet structure for UAP communication"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "optimize",
                "goal": "optimize HVAC pricebook",
                "context_ref": "BellOps/v1.2",
                "priority": 0.8,
                "deadline": "2024-01-15T10:00:00Z",
                "metadata": {
                    "domain": "hvac",
                    "organization": "BellOps",
                    "version": "1.2"
                },
                "created_at": "2024-01-01T10:00:00Z"
            }
        }
    )
    
    id: UUID = Field(default_factory=uuid4, description="Unique intent identifier")
    type: IntentType = Field(description="Type of intent")
    goal: str = Field(description="Natural language description of the goal")
    context_ref: Optional[str] = Field(None, description="Reference to context schema version")
    priority: float = Field(default=0.5, ge=0.0, le=1.0, description="Intent priority (0-1)")
    deadline: Optional[datetime] = Field(None, description="Optional deadline for completion")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    
    def to_json_ld(self) -> Dict[str, Any]:
        """Convert to JSON-LD format for semantic interoperability"""
        return {
            "@context": {
                "@vocab": "https://uap.dev/schema#",
                "uap": "https://uap.dev/schema#"
            },
            "@type": "uap:IntentPacket",
            "@id": str(self.id),
            "uap:type": self.type.value,
            "uap:goal": self.goal,
            "uap:contextRef": self.context_ref,
            "uap:priority": self.priority,
            "uap:deadline": self.deadline.isoformat() if self.deadline else None,
            "uap:metadata": self.metadata,
            "uap:createdAt": self.created_at.isoformat()
        }
    
    @classmethod
    def from_json_ld(cls, data: Dict[str, Any]) -> "IntentPacket":
        """Create from JSON-LD format"""
        return cls(
            id=UUID(data["@id"]),
            type=IntentType(data["uap:type"]),
            goal=data["uap:goal"],
            context_ref=data.get("uap:contextRef"),
            priority=data["uap:priority"],
            deadline=datetime.fromisoformat(data["uap:deadline"]) if data.get("uap:deadline") else None,
            metadata=data.get("uap:metadata", {}),
            created_at=datetime.fromisoformat(data["uap:createdAt"])
        )
