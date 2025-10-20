"""Memory + Reflection Engine - Core of Layer 3"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from ..models.memory_stream import MemoryStream, MemoryQuery, MemoryGranularity, RetentionPolicy
from ..models.reflection import ReflectionReport, EvaluationResult
from ..storage.memory_bus import MemoryBus
from ..storage.postgres_client import PostgreSQLClient
from .auditor import DecisionAuditor
from .critic import OutcomeCritic
from .optimizer import RoutingOptimizer


@dataclass
class ReflectionContext:
    """Context for reflection operations"""
    actor: str
    intent: Dict[str, Any]
    result: Dict[str, Any]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    execution_time: float = 0.0
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ReflectionEngine:
    """Memory + reflection engine for decision auditing and optimization"""
    
    def __init__(
        self,
        memory_bus: MemoryBus,
        postgres_client: PostgreSQLClient,
        audit_window: int = 3600,  # 1 hour
        reflection_interval: int = 300  # 5 minutes
    ):
        self.memory_bus = memory_bus
        self.postgres_client = postgres_client
        self.audit_window = audit_window
        self.reflection_interval = reflection_interval
        
        # Initialize components
        self.auditor = DecisionAuditor(postgres_client)
        self.critic = OutcomeCritic()
        self.optimizer = RoutingOptimizer(postgres_client)
        
        # Background tasks
        self._reflection_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the reflection engine"""
        if self._reflection_task is None:
            self._reflection_task = asyncio.create_task(self._reflection_loop())
        
        if self._optimization_task is None:
            self._optimization_task = asyncio.create_task(self._optimization_loop())
    
    async def stop(self) -> None:
        """Stop the reflection engine"""
        if self._reflection_task:
            self._reflection_task.cancel()
            try:
                await self._reflection_task
            except asyncio.CancelledError:
                pass
            self._reflection_task = None
        
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
            self._optimization_task = None
    
    async def reflect_on_decision(
        self,
        context: ReflectionContext
    ) -> ReflectionReport:
        """Reflect on a decision and generate insights"""
        
        # Store memory of the decision
        memory = MemoryStream(
            stream_id=f"reflection/{context.actor}/{context.timestamp.strftime('%Y%m%d')}",
            actor=context.actor,
            intent=context.intent,
            context={"performance_metrics": context.performance_metrics},
            result=context.result,
            confidence=context.confidence,
            next_action="Reflect and optimize",
            granularity=MemoryGranularity.TASK,
            retention_policy=RetentionPolicy.PERMANENT
        )
        
        await self.memory_bus.store_memory(memory)
        
        # Audit the decision
        audit_result = await self.auditor.audit_decision(context)
        
        # Evaluate the outcome
        evaluation = await self.critic.evaluate_outcome(context, audit_result)
        
        # Generate recommendations
        recommendations = await self.optimizer.generate_recommendations(
            context, evaluation
        )
        
        # Create reflection report
        report = ReflectionReport(
            report_id=f"reflection-{context.actor}-{context.timestamp.strftime('%Y%m%d-%H%M%S')}",
            actor=context.actor,
            intent=context.intent,
            context={"performance_metrics": context.performance_metrics},
            result=context.result,
            confidence=context.confidence,
            next_action="Apply recommendations",
            evaluation=evaluation,
            recommendations=recommendations
        )
        
        # Store reflection report
        await self.postgres_client.create_reflection_report(
            report_id=report.report_id,
            actor=report.actor,
            intent=report.intent,
            context={"performance_metrics": context.performance_metrics},
            result=report.result,
            confidence=report.confidence,
            next_action=report.next_action,
            evaluation=evaluation.dict(),
            recommendations=recommendations
        )
        
        return report
    
    async def get_performance_insights(
        self,
        actor: Optional[str] = None,
        time_window: int = 3600
    ) -> Dict[str, Any]:
        """Get performance insights for an actor or system-wide"""
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(seconds=time_window)
        
        # Query reflection reports
        reports = await self.postgres_client.get_reflection_reports(
            actor=actor,
            limit=1000
        )
        
        if not reports:
            return {"insights": [], "summary": {}}
        
        # Analyze performance trends
        insights = []
        total_reports = len(reports)
        avg_confidence = sum(r.get("confidence", 0) for r in reports) / total_reports
        avg_score = sum(
            r.get("evaluation", {}).get("score", 0) for r in reports
        ) / total_reports
        
        # Performance trends
        recent_reports = [r for r in reports if r.get("created_at", datetime.min) > start_time]
        if len(recent_reports) > 1:
            recent_avg = sum(
                r.get("evaluation", {}).get("score", 0) for r in recent_reports
            ) / len(recent_reports)
            
            if recent_avg > avg_score:
                insights.append({
                    "type": "improvement",
                    "message": "Performance is improving over time",
                    "trend": "positive"
                })
            elif recent_avg < avg_score:
                insights.append({
                    "type": "decline",
                    "message": "Performance is declining over time",
                    "trend": "negative"
                })
        
        # Common recommendations
        all_recommendations = []
        for report in reports:
            recs = report.get("recommendations", {})
            if "routing_changes" in recs:
                all_recommendations.extend(recs["routing_changes"])
        
        # Find most common recommendations
        if all_recommendations:
            common_recs = {}
            for rec in all_recommendations:
                node_id = rec.get("node_id", "unknown")
                if node_id not in common_recs:
                    common_recs[node_id] = 0
                common_recs[node_id] += 1
            
            most_common = max(common_recs.items(), key=lambda x: x[1])
            insights.append({
                "type": "recommendation",
                "message": f"Node {most_common[0]} needs optimization (mentioned {most_common[1]} times)",
                "priority": "high" if most_common[1] > 3 else "medium"
            })
        
        return {
            "insights": insights,
            "summary": {
                "total_reports": total_reports,
                "average_confidence": avg_confidence,
                "average_score": avg_score,
                "time_window_hours": time_window / 3600
            }
        }
    
    async def _reflection_loop(self) -> None:
        """Background reflection loop"""
        while True:
            try:
                await asyncio.sleep(self.reflection_interval)
                await self._perform_reflection()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Reflection loop error: {e}")
    
    async def _optimization_loop(self) -> None:
        """Background optimization loop"""
        while True:
            try:
                await asyncio.sleep(self.reflection_interval * 2)  # Run less frequently
                await self._perform_optimization()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Optimization loop error: {e}")
    
    async def _perform_reflection(self) -> None:
        """Perform periodic reflection on recent decisions"""
        # Get recent memories that need reflection
        query = MemoryQuery(
            granularity=[MemoryGranularity.TASK],
            retention_policy=[RetentionPolicy.PERMANENT],
            limit=100
        )
        
        memories = await self.memory_bus.query_memories(query)
        
        # Reflect on memories that don't have reflection reports yet
        for memory in memories:
            # Check if reflection report already exists
            reports = await self.postgres_client.get_reflection_reports(
                actor=memory.actor,
                limit=1
            )
            
            if not reports:
                # Create reflection context
                context = ReflectionContext(
                    actor=memory.actor,
                    intent=memory.intent,
                    result=memory.result or {},
                    confidence=memory.confidence or 0.0,
                    timestamp=memory.created_at
                )
                
                # Perform reflection
                await self.reflect_on_decision(context)
    
    async def _perform_optimization(self) -> None:
        """Perform periodic optimization based on reflection data"""
        # Get recent reflection reports
        reports = await self.postgres_client.get_reflection_reports(limit=100)
        
        if not reports:
            return
        
        # Analyze performance patterns
        performance_data = {}
        for report in reports:
            actor = report.get("actor", "unknown")
            if actor not in performance_data:
                performance_data[actor] = []
            
            evaluation = report.get("evaluation", {})
            performance_data[actor].append({
                "score": evaluation.get("score", 0),
                "confidence": report.get("confidence", 0),
                "timestamp": report.get("created_at")
            })
        
        # Apply optimizations
        for actor, data in performance_data.items():
            if len(data) >= 5:  # Need sufficient data
                avg_score = sum(d["score"] for d in data) / len(data)
                if avg_score < 0.7:  # Poor performance threshold
                    await self.optimizer.optimize_actor_routing(actor, data)
