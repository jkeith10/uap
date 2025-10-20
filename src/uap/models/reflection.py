"""Reflection Report Models"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict


class EvaluationResult(BaseModel):
    """Result of an evaluation process"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "score": 0.85,
                "metrics": {
                    "accuracy": 0.92,
                    "efficiency": 0.78,
                    "cost_effectiveness": 0.88
                },
                "feedback": "Good performance with room for improvement in efficiency",
                "recommendations": [
                    "Optimize data collection process",
                    "Consider caching frequently accessed data"
                ]
            }
        }
    )
    
    score: float = Field(ge=0.0, le=1.0, description="Overall evaluation score")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Detailed metrics")
    feedback: Optional[str] = Field(None, description="Human-readable feedback")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional evaluation metadata")


class ReflectionReport(BaseModel):
    """Reflection report for decision auditing and optimization"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "report_id": "reflection-001",
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
                "evaluation": {
                    "score": 0.85,
                    "metrics": {
                        "accuracy": 0.92,
                        "efficiency": 0.78
                    },
                    "feedback": "Good performance with room for improvement",
                    "recommendations": ["Optimize data collection"]
                },
                "recommendations": {
                    "routing_changes": [
                        {
                            "node_id": "pricing_analyzer",
                            "weight_adjustment": 0.1,
                            "reason": "Improved accuracy observed"
                        }
                    ],
                    "parameter_tuning": {
                        "confidence_threshold": 0.85,
                        "timeout_multiplier": 1.2
                    }
                },
                "created_at": "2024-01-01T10:00:00Z"
            }
        }
    )
    
    id: UUID = Field(default_factory=uuid4, description="Unique report identifier")
    report_id: str = Field(description="Human-readable report identifier")
    actor: str = Field(description="Actor that generated this report")
    intent: Dict[str, Any] = Field(description="Original intent that was evaluated")
    context: Optional[Dict[str, Any]] = Field(None, description="Contextual information")
    result: Optional[Dict[str, Any]] = Field(None, description="Result of the action")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    next_action: Optional[str] = Field(None, description="Suggested next action")
    evaluation: EvaluationResult = Field(description="Evaluation results")
    recommendations: Dict[str, Any] = Field(default_factory=dict, description="Optimization recommendations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    
    def to_json_ld(self) -> Dict[str, Any]:
        """Convert to JSON-LD format for semantic interoperability"""
        return {
            "@context": {
                "@vocab": "https://uap.dev/schema#",
                "uap": "https://uap.dev/schema#"
            },
            "@type": "uap:ReflectionReport",
            "@id": str(self.id),
            "uap:reportId": self.report_id,
            "uap:actor": self.actor,
            "uap:intent": self.intent,
            "uap:context": self.context,
            "uap:result": self.result,
            "uap:confidence": self.confidence,
            "uap:nextAction": self.next_action,
            "uap:evaluation": {
                "uap:score": self.evaluation.score,
                "uap:metrics": self.evaluation.metrics,
                "uap:feedback": self.evaluation.feedback,
                "uap:recommendations": self.evaluation.recommendations,
                "uap:metadata": self.evaluation.metadata
            },
            "uap:recommendations": self.recommendations,
            "uap:metadata": self.metadata,
            "uap:createdAt": self.created_at.isoformat()
        }
    
    @classmethod
    def from_json_ld(cls, data: Dict[str, Any]) -> "ReflectionReport":
        """Create from JSON-LD format"""
        eval_data = data["uap:evaluation"]
        evaluation = EvaluationResult(
            score=eval_data["uap:score"],
            metrics=eval_data.get("uap:metrics", {}),
            feedback=eval_data.get("uap:feedback"),
            recommendations=eval_data.get("uap:recommendations", []),
            metadata=eval_data.get("uap:metadata", {})
        )
        
        return cls(
            id=UUID(data["@id"]),
            report_id=data["uap:reportId"],
            actor=data["uap:actor"],
            intent=data["uap:intent"],
            context=data.get("uap:context"),
            result=data.get("uap:result"),
            confidence=data.get("uap:confidence"),
            next_action=data.get("uap:nextAction"),
            evaluation=evaluation,
            recommendations=data.get("uap:recommendations", {}),
            metadata=data.get("uap:metadata", {}),
            created_at=datetime.fromisoformat(data["uap:createdAt"])
        )
    
    def get_routing_recommendations(self) -> List[Dict[str, Any]]:
        """Extract routing recommendations from the report"""
        return self.recommendations.get("routing_changes", [])
    
    def get_parameter_recommendations(self) -> Dict[str, Any]:
        """Extract parameter tuning recommendations from the report"""
        return self.recommendations.get("parameter_tuning", {})
    
    def should_trigger_optimization(self, threshold: float = 0.7) -> bool:
        """Determine if this report should trigger optimization based on score"""
        return self.evaluation.score < threshold


class ReflectionQuery(BaseModel):
    """Query structure for reflection reports"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "actors": ["Agent:BellOps.Worker"],
                "time_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-31T23:59:59Z"
                },
                "score_threshold": 0.7,
                "limit": 50
            }
        }
    )
    
    actors: Optional[List[str]] = Field(None, description="Actors to filter by")
    time_range: Optional[Dict[str, datetime]] = Field(None, description="Time range filter")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum evaluation score")
    intent_filters: Optional[Dict[str, Any]] = Field(None, description="Intent-based filters")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    
    def to_sql_where_clause(self) -> tuple[str, Dict[str, Any]]:
        """Convert to SQL WHERE clause and parameters"""
        conditions = []
        params = {}
        
        if self.actors:
            actor_conditions = []
            for i, actor in enumerate(self.actors):
                actor_conditions.append(f"actor = :actor_{i}")
                params[f"actor_{i}"] = actor
            conditions.append(f"({' OR '.join(actor_conditions)})")
        
        if self.time_range:
            if "start" in self.time_range:
                conditions.append("created_at >= :time_start")
                params["time_start"] = self.time_range["start"]
            if "end" in self.time_range:
                conditions.append("created_at <= :time_end")
                params["time_end"] = self.time_range["end"]
        
        if self.score_threshold is not None:
            conditions.append("evaluation->>'score' >= :score_threshold")
            params["score_threshold"] = self.score_threshold
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params
