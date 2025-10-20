"""Outcome Critic - Evaluates decision outcomes and provides feedback"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

from ..models.reflection import EvaluationResult


@dataclass
class OutcomeMetrics:
    """Metrics for evaluating outcomes"""
    accuracy: float
    efficiency: float
    cost_effectiveness: float
    user_satisfaction: float
    system_performance: float
    reliability: float


class OutcomeCritic:
    """Evaluates outcomes and provides critical feedback"""
    
    def __init__(self):
        self._evaluation_cache: Dict[str, EvaluationResult] = {}
        self._baseline_metrics = {
            "accuracy": 0.8,
            "efficiency": 0.7,
            "cost_effectiveness": 0.75,
            "user_satisfaction": 0.8,
            "system_performance": 0.85,
            "reliability": 0.9
        }
    
    async def evaluate_outcome(
        self,
        context: Any,  # ReflectionContext from engine
        audit_result: Dict[str, Any]
    ) -> EvaluationResult:
        """Evaluate the outcome of a decision"""
        
        # Extract metrics from context
        metrics = context.performance_metrics or {}
        
        # Calculate individual metric scores
        accuracy = self._calculate_accuracy_score(context, metrics)
        efficiency = self._calculate_efficiency_score(context, metrics)
        cost_effectiveness = self._calculate_cost_effectiveness_score(context, metrics)
        
        # Calculate overall score
        overall_score = (accuracy + efficiency + cost_effectiveness) / 3
        
        # Generate feedback
        feedback = self._generate_feedback(overall_score, metrics, audit_result)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(overall_score, metrics, audit_result)
        
        # Create evaluation result
        evaluation = EvaluationResult(
            score=overall_score,
            metrics={
                "accuracy": accuracy,
                "efficiency": efficiency,
                "cost_effectiveness": cost_effectiveness,
                "execution_time": context.execution_time,
                "confidence": context.confidence
            },
            feedback=feedback,
            recommendations=recommendations,
            metadata={
                "audit_score": audit_result.get("audit_score", 0),
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Cache evaluation
        evaluation_key = f"{context.actor}-{context.timestamp.strftime('%Y%m%d-%H%M%S')}"
        self._evaluation_cache[evaluation_key] = evaluation
        
        return evaluation
    
    async def get_evaluation_history(
        self,
        actor: Optional[str] = None,
        limit: int = 100
    ) -> List[EvaluationResult]:
        """Get evaluation history for analysis"""
        
        evaluations = []
        for key, evaluation in self._evaluation_cache.items():
            if actor is None or key.startswith(actor):
                evaluations.append(evaluation)
        
        # Sort by timestamp (newest first)
        evaluations.sort(
            key=lambda x: x.metadata.get("evaluation_timestamp", ""),
            reverse=True
        )
        
        return evaluations[:limit]
    
    async def analyze_performance_trends(
        self,
        actor: Optional[str] = None,
        time_window: int = 86400  # 24 hours
    ) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        
        evaluations = await self.get_evaluation_history(actor)
        
        if len(evaluations) < 2:
            return {"trends": [], "summary": {}}
        
        # Calculate trends
        scores = [e.score for e in evaluations]
        accuracies = [e.metrics.get("accuracy", 0) for e in evaluations]
        efficiencies = [e.metrics.get("efficiency", 0) for e in evaluations]
        
        # Calculate trend direction
        score_trend = self._calculate_trend(scores)
        accuracy_trend = self._calculate_trend(accuracies)
        efficiency_trend = self._calculate_trend(efficiencies)
        
        trends = []
        
        if score_trend > 0.1:
            trends.append({
                "metric": "overall_score",
                "direction": "improving",
                "magnitude": score_trend,
                "description": "Overall performance is improving"
            })
        elif score_trend < -0.1:
            trends.append({
                "metric": "overall_score",
                "direction": "declining",
                "magnitude": abs(score_trend),
                "description": "Overall performance is declining"
            })
        
        if accuracy_trend > 0.1:
            trends.append({
                "metric": "accuracy",
                "direction": "improving",
                "magnitude": accuracy_trend,
                "description": "Decision accuracy is improving"
            })
        elif accuracy_trend < -0.1:
            trends.append({
                "metric": "accuracy",
                "direction": "declining",
                "magnitude": abs(accuracy_trend),
                "description": "Decision accuracy is declining"
            })
        
        return {
            "trends": trends,
            "summary": {
                "total_evaluations": len(evaluations),
                "average_score": sum(scores) / len(scores),
                "average_accuracy": sum(accuracies) / len(accuracies),
                "average_efficiency": sum(efficiencies) / len(efficiencies),
                "time_window_hours": time_window / 3600
            }
        }
    
    def _calculate_accuracy_score(self, context: Any, metrics: Dict[str, float]) -> float:
        """Calculate accuracy score based on context and metrics"""
        
        # Base accuracy on confidence and result quality
        base_accuracy = context.confidence
        
        # Adjust based on performance metrics
        if "accuracy" in metrics:
            base_accuracy = (base_accuracy + metrics["accuracy"]) / 2
        
        # Check if result is complete
        if context.result and len(context.result) > 0:
            base_accuracy *= 1.1  # Bonus for complete results
        
        return min(base_accuracy, 1.0)
    
    def _calculate_efficiency_score(self, context: Any, metrics: Dict[str, float]) -> float:
        """Calculate efficiency score"""
        
        # Base efficiency on execution time
        if context.execution_time > 0:
            # Normalize execution time (assume 1 second is optimal)
            efficiency = max(0, 1.0 - (context.execution_time - 1.0) / 10.0)
        else:
            efficiency = 0.5  # Default if no execution time
        
        # Adjust based on performance metrics
        if "efficiency" in metrics:
            efficiency = (efficiency + metrics["efficiency"]) / 2
        
        return min(efficiency, 1.0)
    
    def _calculate_cost_effectiveness_score(self, context: Any, metrics: Dict[str, float]) -> float:
        """Calculate cost-effectiveness score"""
        
        # Base score on confidence vs execution time
        if context.execution_time > 0:
            cost_effectiveness = context.confidence / (1.0 + context.execution_time / 10.0)
        else:
            cost_effectiveness = context.confidence * 0.8
        
        # Adjust based on performance metrics
        if "cost_effectiveness" in metrics:
            cost_effectiveness = (cost_effectiveness + metrics["cost_effectiveness"]) / 2
        
        return min(cost_effectiveness, 1.0)
    
    def _generate_feedback(self, score: float, metrics: Dict[str, float], audit_result: Dict[str, Any]) -> str:
        """Generate human-readable feedback"""
        
        if score >= 0.9:
            return "Excellent performance with high accuracy and efficiency"
        elif score >= 0.8:
            return "Good performance with room for minor improvements"
        elif score >= 0.7:
            return "Acceptable performance with some areas for improvement"
        elif score >= 0.6:
            return "Below average performance requiring attention"
        else:
            return "Poor performance requiring immediate optimization"
    
    def _generate_recommendations(self, score: float, metrics: Dict[str, float], audit_result: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        if score < 0.8:
            recommendations.append("Review and optimize decision algorithms")
        
        if metrics.get("accuracy", 1.0) < 0.8:
            recommendations.append("Improve training data quality and model accuracy")
        
        if metrics.get("efficiency", 1.0) < 0.7:
            recommendations.append("Optimize execution time and resource usage")
        
        if context.execution_time > 5.0:
            recommendations.append("Consider caching or parallel processing")
        
        if audit_result.get("audit_score", 1.0) < 0.7:
            recommendations.append("Address audit issues and improve decision quality")
        
        if not recommendations:
            recommendations.append("Continue monitoring and maintain current performance")
        
        return recommendations
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction and magnitude"""
        
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        if n * x2_sum - x_sum * x_sum == 0:
            return 0.0
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        return slope
