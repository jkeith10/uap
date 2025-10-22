"""Unit tests for UAP reflection components"""

import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from uap.reflection.critic import OutcomeCritic, OutcomeMetrics
from uap.reflection.optimizer import RoutingOptimizer, OptimizationRecommendation


class TestOutcomeCritic:
    """Test outcome critic"""
    
    def test_create_critic(self):
        """Test creating outcome critic"""
        critic = OutcomeCritic()
        
        assert critic is not None
        assert len(critic._baseline_metrics) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_outcome(self, mock_postgres_client):
        """Test outcome evaluation"""
        from dataclasses import dataclass
        
        @dataclass
        class MockContext:
            actor: str = "test-actor"
            intent: dict = None
            result: dict = None
            performance_metrics: dict = None
            execution_time: float = 1.0
            confidence: float = 0.9
            timestamp: datetime = None
            
            def __post_init__(self):
                if self.intent is None:
                    self.intent = {}
                if self.result is None:
                    self.result = {}
                if self.performance_metrics is None:
                    self.performance_metrics = {}
                if self.timestamp is None:
                    self.timestamp = datetime.now(timezone.utc)
        
        critic = OutcomeCritic()
        context = MockContext()
        audit_result = {"audit_score": 0.85}
        
        evaluation = await critic.evaluate_outcome(context, audit_result)
        
        assert evaluation is not None
        assert evaluation.score >= 0.0
        assert evaluation.score <= 1.0
        assert len(evaluation.metrics) > 0
        assert evaluation.feedback is not None


class TestRoutingOptimizer:
    """Test routing optimizer"""
    
    def test_create_optimizer(self, mock_postgres_client):
        """Test creating routing optimizer"""
        optimizer = RoutingOptimizer(mock_postgres_client)
        
        assert optimizer is not None
        assert optimizer.postgres_client == mock_postgres_client
    
    def test_optimization_recommendation(self):
        """Test optimization recommendation"""
        rec = OptimizationRecommendation(
            type="routing",
            target="node-1",
            action="increase",
            value=0.1,
            reason="Improved performance",
            priority="high",
            expected_impact=0.15
        )
        
        assert rec.type == "routing"
        assert rec.target == "node-1"
        assert rec.priority == "high"
        assert rec.expected_impact == 0.15

