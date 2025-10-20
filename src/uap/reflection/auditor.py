"""Decision Auditor - Tracks all interactions with Universal Reflection Schema"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from ..storage.postgres_client import PostgreSQLClient


@dataclass
class DecisionRecord:
    """Record of a decision made by the system"""
    decision_id: str
    actor: str
    intent: Dict[str, Any]
    context: Dict[str, Any]
    decision: Dict[str, Any]
    reasoning: str
    confidence: float
    timestamp: datetime
    outcome: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, float]] = None


class DecisionAuditor:
    """Audits all decisions made by the UAP system"""
    
    def __init__(self, postgres_client: PostgreSQLClient):
        self.postgres_client = postgres_client
        self._decision_cache: Dict[str, DecisionRecord] = {}
    
    async def audit_decision(
        self,
        context: Any  # ReflectionContext from engine
    ) -> Dict[str, Any]:
        """Audit a decision and return audit results"""
        
        # Create decision record
        decision_record = DecisionRecord(
            decision_id=f"decision-{context.actor}-{context.timestamp.strftime('%Y%m%d-%H%M%S')}",
            actor=context.actor,
            intent=context.intent,
            context={"performance_metrics": context.performance_metrics},
            decision=context.result,
            reasoning="Automated decision based on intent and context",
            confidence=context.confidence,
            timestamp=context.timestamp,
            outcome=context.result,
            performance_metrics=context.performance_metrics
        )
        
        # Store in cache
        self._decision_cache[decision_record.decision_id] = decision_record
        
        # Store in database
        await self._store_decision_record(decision_record)
        
        # Analyze decision quality
        audit_result = await self._analyze_decision_quality(decision_record)
        
        return {
            "decision_id": decision_record.decision_id,
            "audit_score": audit_result["score"],
            "issues": audit_result["issues"],
            "recommendations": audit_result["recommendations"],
            "timestamp": decision_record.timestamp.isoformat()
        }
    
    async def get_decision_history(
        self,
        actor: Optional[str] = None,
        time_window: int = 3600,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get decision history for analysis"""
        
        # For now, return cached decisions
        # In a real implementation, this would query the database
        decisions = []
        
        for decision in self._decision_cache.values():
            if actor is None or decision.actor == actor:
                decisions.append({
                    "decision_id": decision.decision_id,
                    "actor": decision.actor,
                    "intent": decision.intent,
                    "decision": decision.decision,
                    "confidence": decision.confidence,
                    "timestamp": decision.timestamp.isoformat(),
                    "outcome": decision.outcome,
                    "performance_metrics": decision.performance_metrics
                })
        
        # Sort by timestamp (newest first)
        decisions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return decisions[:limit]
    
    async def analyze_decision_patterns(
        self,
        actor: Optional[str] = None,
        time_window: int = 86400  # 24 hours
    ) -> Dict[str, Any]:
        """Analyze patterns in decision making"""
        
        decisions = await self.get_decision_history(actor, time_window)
        
        if not decisions:
            return {"patterns": [], "summary": {}}
        
        # Analyze confidence patterns
        confidences = [d["confidence"] for d in decisions]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Analyze intent patterns
        intent_types = {}
        for decision in decisions:
            intent_type = decision["intent"].get("type", "unknown")
            intent_types[intent_type] = intent_types.get(intent_type, 0) + 1
        
        # Analyze performance patterns
        performance_scores = []
        for decision in decisions:
            if decision.get("performance_metrics"):
                score = decision["performance_metrics"].get("score", 0)
                performance_scores.append(score)
        
        avg_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0
        
        # Identify patterns
        patterns = []
        
        if avg_confidence < 0.7:
            patterns.append({
                "type": "low_confidence",
                "description": "Decisions show consistently low confidence",
                "severity": "high",
                "recommendation": "Review decision logic and training data"
            })
        
        if avg_performance < 0.6:
            patterns.append({
                "type": "poor_performance",
                "description": "Decisions show poor performance outcomes",
                "severity": "high",
                "recommendation": "Optimize decision algorithms"
            })
        
        # Check for decision frequency patterns
        if len(decisions) > 100:  # High frequency
            patterns.append({
                "type": "high_frequency",
                "description": "High frequency of decisions",
                "severity": "medium",
                "recommendation": "Consider caching or batching decisions"
            })
        
        return {
            "patterns": patterns,
            "summary": {
                "total_decisions": len(decisions),
                "average_confidence": avg_confidence,
                "average_performance": avg_performance,
                "intent_distribution": intent_types,
                "time_window_hours": time_window / 3600
            }
        }
    
    async def _store_decision_record(self, record: DecisionRecord) -> None:
        """Store decision record in database"""
        # In a real implementation, this would store in a decisions table
        # For now, we'll use the reflection_reports table
        await self.postgres_client.create_reflection_report(
            report_id=record.decision_id,
            actor=record.actor,
            intent=record.intent,
            context=record.context,
            result=record.decision,
            confidence=record.confidence,
            next_action="Audit decision",
            evaluation={
                "score": record.confidence,
                "metrics": record.performance_metrics or {},
                "feedback": f"Decision audit for {record.actor}",
                "recommendations": []
            },
            recommendations={
                "audit_type": "decision_audit",
                "reasoning": record.reasoning
            }
        )
    
    async def _analyze_decision_quality(self, record: DecisionRecord) -> Dict[str, Any]:
        """Analyze the quality of a decision"""
        
        issues = []
        recommendations = []
        score = record.confidence
        
        # Check confidence level
        if record.confidence < 0.5:
            issues.append("Very low confidence in decision")
            recommendations.append("Review decision criteria and training data")
            score *= 0.8
        
        # Check for missing context
        if not record.context or not record.context.get("performance_metrics"):
            issues.append("Missing performance context")
            recommendations.append("Ensure complete context is available")
            score *= 0.9
        
        # Check decision completeness
        if not record.decision or len(record.decision) == 0:
            issues.append("Incomplete decision")
            recommendations.append("Ensure decision includes all required elements")
            score *= 0.7
        
        # Check reasoning quality
        if not record.reasoning or len(record.reasoning) < 10:
            issues.append("Insufficient reasoning provided")
            recommendations.append("Provide detailed reasoning for decisions")
            score *= 0.9
        
        return {
            "score": min(score, 1.0),
            "issues": issues,
            "recommendations": recommendations
        }
