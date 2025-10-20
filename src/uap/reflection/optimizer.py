"""Routing Optimizer - Auto-tunes collaboration networks based on performance"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from ..storage.postgres_client import PostgreSQLClient


@dataclass
class OptimizationRecommendation:
    """Recommendation for system optimization"""
    type: str  # "routing", "parameter", "architecture"
    target: str  # Node ID, parameter name, etc.
    action: str  # "increase", "decrease", "replace", "add"
    value: Any  # New value or adjustment
    reason: str  # Explanation for the recommendation
    priority: str  # "low", "medium", "high", "critical"
    expected_impact: float  # Expected performance improvement


class RoutingOptimizer:
    """Optimizes routing and system parameters based on performance data"""
    
    def __init__(self, postgres_client: PostgreSQLClient):
        self.postgres_client = postgres_client
        self._optimization_history: List[Dict[str, Any]] = []
        self._performance_baselines: Dict[str, float] = {}
    
    async def generate_recommendations(
        self,
        context: Any,  # ReflectionContext from engine
        evaluation: Any  # EvaluationResult from critic
    ) -> Dict[str, Any]:
        """Generate optimization recommendations based on evaluation"""
        
        recommendations = {
            "routing_changes": [],
            "parameter_tuning": {},
            "architecture_changes": [],
            "priority": "medium"
        }
        
        # Analyze performance and generate recommendations
        if evaluation.score < 0.7:
            # Poor performance - need significant changes
            recommendations["priority"] = "high"
            
            # Routing optimization
            routing_recs = await self._analyze_routing_performance(context, evaluation)
            recommendations["routing_changes"].extend(routing_recs)
            
            # Parameter tuning
            param_recs = await self._analyze_parameter_performance(context, evaluation)
            recommendations["parameter_tuning"].update(param_recs)
            
            # Architecture changes
            arch_recs = await self._analyze_architecture_performance(context, evaluation)
            recommendations["architecture_changes"].extend(arch_recs)
        
        elif evaluation.score < 0.8:
            # Moderate performance - minor optimizations
            recommendations["priority"] = "medium"
            
            # Minor routing adjustments
            routing_recs = await self._analyze_routing_performance(context, evaluation)
            recommendations["routing_changes"].extend(routing_recs[:2])  # Limit to top 2
            
            # Parameter fine-tuning
            param_recs = await self._analyze_parameter_performance(context, evaluation)
            recommendations["parameter_tuning"].update(param_recs)
        
        else:
            # Good performance - maintenance recommendations
            recommendations["priority"] = "low"
            recommendations["routing_changes"].append({
                "node_id": context.actor,
                "weight_adjustment": 0.05,
                "reason": "Maintain current performance with minor optimization"
            })
        
        # Store optimization history
        self._optimization_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": context.actor,
            "evaluation_score": evaluation.score,
            "recommendations": recommendations,
            "context": context.intent
        })
        
        return recommendations
    
    async def optimize_actor_routing(
        self,
        actor: str,
        performance_data: List[Dict[str, Any]]
    ) -> List[OptimizationRecommendation]:
        """Optimize routing for a specific actor based on performance data"""
        
        recommendations = []
        
        if not performance_data:
            return recommendations
        
        # Calculate average performance
        avg_score = sum(d["score"] for d in performance_data) / len(performance_data)
        avg_confidence = sum(d["confidence"] for d in performance_data) / len(performance_data)
        
        # Get current node capabilities
        node_data = await self.postgres_client.get_node_capabilities(actor)
        
        if not node_data:
            return recommendations
        
        node_info = node_data[0]
        current_weights = {
            "cost_weight": node_info["cost_weight"],
            "latency_weight": node_info["latency_weight"],
            "confidence_weight": node_info["confidence_weight"]
        }
        
        # Analyze performance patterns
        if avg_score < 0.6:
            # Poor performance - significant adjustments needed
            if avg_confidence < 0.7:
                recommendations.append(OptimizationRecommendation(
                    type="parameter",
                    target="confidence_weight",
                    action="decrease",
                    value=current_weights["confidence_weight"] * 0.8,
                    reason="Low confidence indicates over-reliance on confidence scoring",
                    priority="high",
                    expected_impact=0.2
                ))
            
            if current_weights["cost_weight"] > 1.0:
                recommendations.append(OptimizationRecommendation(
                    type="parameter",
                    target="cost_weight",
                    action="decrease",
                    value=current_weights["cost_weight"] * 0.9,
                    reason="High cost weight may be limiting performance",
                    priority="medium",
                    expected_impact=0.1
                ))
        
        elif avg_score < 0.8:
            # Moderate performance - fine-tuning
            if avg_confidence > 0.9:
                recommendations.append(OptimizationRecommendation(
                    type="parameter",
                    target="confidence_weight",
                    action="increase",
                    value=current_weights["confidence_weight"] * 1.1,
                    reason="High confidence suggests good decision quality",
                    priority="low",
                    expected_impact=0.05
                ))
        
        # Analyze execution time patterns
        execution_times = [d.get("execution_time", 0) for d in performance_data if d.get("execution_time")]
        if execution_times:
            avg_execution_time = sum(execution_times) / len(execution_times)
            
            if avg_execution_time > 5.0:
                recommendations.append(OptimizationRecommendation(
                    type="architecture",
                    target="execution_time",
                    action="optimize",
                    value="caching",
                    reason="High execution time suggests need for caching or parallel processing",
                    priority="medium",
                    expected_impact=0.15
                ))
        
        return recommendations
    
    async def apply_optimization(
        self,
        recommendation: OptimizationRecommendation
    ) -> bool:
        """Apply an optimization recommendation"""
        
        try:
            if recommendation.type == "parameter":
                await self._apply_parameter_optimization(recommendation)
            elif recommendation.type == "routing":
                await self._apply_routing_optimization(recommendation)
            elif recommendation.type == "architecture":
                await self._apply_architecture_optimization(recommendation)
            
            # Record the optimization
            self._optimization_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "optimization_applied",
                "recommendation": recommendation.__dict__,
                "status": "success"
            })
            
            return True
        
        except Exception as e:
            # Record failed optimization
            self._optimization_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "optimization_failed",
                "recommendation": recommendation.__dict__,
                "error": str(e),
                "status": "failed"
            })
            
            return False
    
    async def get_optimization_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get optimization history"""
        
        return self._optimization_history[-limit:]
    
    async def _analyze_routing_performance(
        self,
        context: Any,
        evaluation: Any
    ) -> List[Dict[str, Any]]:
        """Analyze routing performance and generate recommendations"""
        
        recommendations = []
        
        # Check if current actor is performing poorly
        if evaluation.score < 0.7:
            recommendations.append({
                "node_id": context.actor,
                "weight_adjustment": -0.1,
                "reason": "Poor performance detected, reducing routing weight"
            })
        
        # Check for alternative nodes that might perform better
        # This would require access to other node performance data
        # For now, we'll make a simple recommendation
        
        if evaluation.metrics.get("efficiency", 1.0) < 0.6:
            recommendations.append({
                "node_id": f"{context.actor}-backup",
                "weight_adjustment": 0.1,
                "reason": "Low efficiency suggests need for backup routing"
            })
        
        return recommendations
    
    async def _analyze_parameter_performance(
        self,
        context: Any,
        evaluation: Any
    ) -> Dict[str, Any]:
        """Analyze parameter performance and generate tuning recommendations"""
        
        parameters = {}
        
        # Adjust confidence threshold based on performance
        if evaluation.score < 0.7:
            parameters["confidence_threshold"] = 0.6  # Lower threshold for poor performers
        elif evaluation.score > 0.9:
            parameters["confidence_threshold"] = 0.9  # Higher threshold for good performers
        else:
            parameters["confidence_threshold"] = 0.8  # Default
        
        # Adjust timeout based on execution time
        if context.execution_time > 5.0:
            parameters["timeout_multiplier"] = 1.5  # Increase timeout
        elif context.execution_time < 1.0:
            parameters["timeout_multiplier"] = 0.8  # Decrease timeout
        else:
            parameters["timeout_multiplier"] = 1.0  # Default
        
        # Adjust retry count based on reliability
        reliability = evaluation.metrics.get("reliability", 0.8)
        if reliability < 0.7:
            parameters["retry_count"] = 5  # More retries for unreliable nodes
        elif reliability > 0.95:
            parameters["retry_count"] = 1  # Fewer retries for reliable nodes
        else:
            parameters["retry_count"] = 3  # Default
        
        return parameters
    
    async def _analyze_architecture_performance(
        self,
        context: Any,
        evaluation: Any
    ) -> List[Dict[str, Any]]:
        """Analyze architecture performance and generate recommendations"""
        
        recommendations = []
        
        # Check for performance bottlenecks
        if context.execution_time > 10.0:
            recommendations.append({
                "type": "caching",
                "description": "Implement caching for frequently accessed data",
                "priority": "high",
                "expected_improvement": 0.3
            })
        
        if evaluation.metrics.get("efficiency", 1.0) < 0.5:
            recommendations.append({
                "type": "parallel_processing",
                "description": "Implement parallel processing for independent tasks",
                "priority": "medium",
                "expected_improvement": 0.2
            })
        
        if evaluation.score < 0.6:
            recommendations.append({
                "type": "load_balancing",
                "description": "Implement load balancing across multiple instances",
                "priority": "high",
                "expected_improvement": 0.25
            })
        
        return recommendations
    
    async def _apply_parameter_optimization(self, recommendation: OptimizationRecommendation) -> None:
        """Apply parameter optimization"""
        
        # Update node capabilities in database
        if recommendation.target in ["cost_weight", "latency_weight", "confidence_weight"]:
            await self.postgres_client.execute(
                f"UPDATE uap.node_capabilities SET {recommendation.target} = $1 WHERE node_id = $2",
                recommendation.value,
                recommendation.target.replace("_weight", "-1")  # Simple mapping
            )
    
    async def _apply_routing_optimization(self, recommendation: OptimizationRecommendation) -> None:
        """Apply routing optimization"""
        
        # This would update routing tables or node weights
        # For now, we'll just log the optimization
        print(f"Applied routing optimization: {recommendation}")
    
    async def _apply_architecture_optimization(self, recommendation: OptimizationRecommendation) -> None:
        """Apply architecture optimization"""
        
        # This would trigger architectural changes
        # For now, we'll just log the optimization
        print(f"Applied architecture optimization: {recommendation}")
