"""Unit tests for UAP models"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.uap.models.intent import IntentPacket, IntentType, IntentPriority
from src.uap.models.action_graph import ActionGraph, ActionNode, GraphStatus
from src.uap.models.memory_stream import MemoryStream, MemoryEntry, MemoryGranularity
from src.uap.models.reflection import ReflectionReport, EvaluationResult, EvaluationType


class TestIntentPacket:
    """Test IntentPacket model"""
    
    def test_create_intent_packet(self):
        """Test creating an intent packet"""
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Test intent",
            context={"test": "value"},
            priority=IntentPriority.HIGH
        )
        
        assert intent.type == IntentType.ACTION
        assert intent.content == "Test intent"
        assert intent.context == {"test": "value"}
        assert intent.priority == IntentPriority.HIGH
        assert intent.id is not None
        assert intent.created_at is not None
    
    def test_intent_packet_serialization(self):
        """Test intent packet serialization"""
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Test intent"
        )
        
        data = intent.model_dump()
        assert "id" in data
        assert "type" in data
        assert "content" in data
        assert "created_at" in data
        
        # Test deserialization
        restored = IntentPacket.model_validate(data)
        assert restored.type == intent.type
        assert restored.content == intent.content
    
    def test_intent_packet_validation(self):
        """Test intent packet validation"""
        with pytest.raises(ValueError):
            IntentPacket(type="invalid_type", content="Test")
        
        with pytest.raises(ValueError):
            IntentPacket(type=IntentType.ACTION, content="")


class TestActionGraph:
    """Test ActionGraph model"""
    
    def test_create_action_graph(self):
        """Test creating an action graph"""
        node = ActionNode(
            type="action",
            data={"action": "test"}
        )
        
        graph = ActionGraph(
            nodes=[node],
            edges=[]
        )
        
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 0
        assert graph.status == GraphStatus.PENDING
        assert graph.id is not None
        assert graph.created_at is not None
    
    def test_action_node_status_update(self):
        """Test action node status update"""
        node = ActionNode(
            type="action",
            data={"action": "test"}
        )
        
        original_updated_at = node.updated_at
        node.update_status(GraphStatus.COMPLETED)
        
        assert node.status == GraphStatus.COMPLETED
        assert node.updated_at > original_updated_at
    
    def test_action_graph_serialization(self):
        """Test action graph serialization"""
        node = ActionNode(type="action", data={"action": "test"})
        graph = ActionGraph(nodes=[node], edges=[])
        
        data = graph.model_dump()
        assert "id" in data
        assert "nodes" in data
        assert "edges" in data
        assert "status" in data
        
        # Test deserialization
        restored = ActionGraph.model_validate(data)
        assert len(restored.nodes) == 1
        assert restored.status == graph.status


class TestMemoryStream:
    """Test MemoryStream model"""
    
    def test_create_memory_stream(self):
        """Test creating a memory stream"""
        entry = MemoryEntry(
            type="event",
            data={"event": "test"}
        )
        
        stream = MemoryStream(
            granularity=MemoryGranularity.SESSION,
            entries=[entry]
        )
        
        assert stream.granularity == MemoryGranularity.SESSION
        assert len(stream.entries) == 1
        assert stream.id is not None
        assert stream.created_at is not None
    
    def test_memory_stream_add_entry(self):
        """Test adding entry to memory stream"""
        stream = MemoryStream(granularity=MemoryGranularity.SESSION)
        
        entry = MemoryEntry(type="event", data={"event": "test"})
        stream.add_entry(entry)
        
        assert len(stream.entries) == 1
        assert stream.entries[0] == entry
    
    def test_memory_stream_serialization(self):
        """Test memory stream serialization"""
        entry = MemoryEntry(type="event", data={"event": "test"})
        stream = MemoryStream(granularity=MemoryGranularity.SESSION, entries=[entry])
        
        data = stream.model_dump()
        assert "id" in data
        assert "granularity" in data
        assert "entries" in data
        
        # Test deserialization
        restored = MemoryStream.model_validate(data)
        assert restored.granularity == stream.granularity
        assert len(restored.entries) == 1


class TestReflectionReport:
    """Test ReflectionReport model"""
    
    def test_create_reflection_report(self):
        """Test creating a reflection report"""
        evaluation = EvaluationResult(
            type=EvaluationType.OUTCOME,
            score=0.8,
            feedback={"test": "feedback"}
        )
        
        report = ReflectionReport(
            type="outcome",
            evaluations=[evaluation]
        )
        
        assert report.type == "outcome"
        assert len(report.evaluations) == 1
        assert report.evaluations[0].score == 0.8
        assert report.id is not None
        assert report.created_at is not None
    
    def test_reflection_report_serialization(self):
        """Test reflection report serialization"""
        evaluation = EvaluationResult(
            type=EvaluationType.OUTCOME,
            score=0.8,
            feedback={"test": "feedback"}
        )
        report = ReflectionReport(type="outcome", evaluations=[evaluation])
        
        data = report.model_dump()
        assert "id" in data
        assert "type" in data
        assert "evaluations" in data
        
        # Test deserialization
        restored = ReflectionReport.model_validate(data)
        assert restored.type == report.type
        assert len(restored.evaluations) == 1
        assert restored.evaluations[0].score == 0.8
