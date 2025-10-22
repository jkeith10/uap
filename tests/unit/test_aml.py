"""Unit tests for UAP AML components"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from uap.aml.packets import UAPContextPacket, PacketType, ProtocolType
from uap.aml.routing import SelfRoutingEngine, CapabilityFingerprint, RoutingScore


class TestUAPContextPacket:
    """Test UAP context packet"""
    
    def test_create_packet(self):
        """Test creating context packet"""
        packet = UAPContextPacket(
            type=PacketType.INTENT,
            source_protocol=ProtocolType.REST,
            target_protocol=ProtocolType.MCP,
            source_node="api",
            target_node="worker",
            payload={"test": "data"}
        )
        
        assert packet.type == PacketType.INTENT
        assert packet.source_protocol == ProtocolType.REST
        assert packet.target_protocol == ProtocolType.MCP
        assert packet.payload["test"] == "data"
    
    def test_to_rest_format(self):
        """Test conversion to REST format"""
        packet = UAPContextPacket(
            type=PacketType.INTENT,
            source_protocol=ProtocolType.REST,
            target_protocol=ProtocolType.REST,
            source_node="api",
            target_node="worker",
            payload={"test": "data"}
        )
        
        rest_data = packet.to_protocol_format(ProtocolType.REST)
        
        assert rest_data["method"] == "POST"
        assert "body" in rest_data
        assert rest_data["body"]["type"] == "intent"
    
    def test_to_mcp_format(self):
        """Test conversion to MCP format"""
        packet = UAPContextPacket(
            type=PacketType.INTENT,
            source_protocol=ProtocolType.REST,
            target_protocol=ProtocolType.MCP,
            source_node="api",
            target_node="worker",
            payload={"test": "data"}
        )
        
        mcp_data = packet.to_protocol_format(ProtocolType.MCP)
        
        assert mcp_data["jsonrpc"] == "2.0"
        assert "method" in mcp_data
        assert "params" in mcp_data
    
    def test_from_rest_format(self):
        """Test creating packet from REST format"""
        rest_data = {
            "body": {
                "packet_id": str(uuid4()),
                "type": "intent",
                "payload": {"test": "data"},
                "metadata": {},
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            "headers": {
                "X-UAP-Source": "api",
                "X-UAP-Target": "worker"
            }
        }
        
        packet = UAPContextPacket.from_protocol_format(rest_data, ProtocolType.REST)
        
        assert packet.type == PacketType.INTENT
        assert packet.source_node == "api"
        assert packet.target_node == "worker"


class TestCapabilityFingerprint:
    """Test capability fingerprint"""
    
    def test_create_fingerprint(self):
        """Test creating capability fingerprint"""
        fingerprint = CapabilityFingerprint(
            node_id="test-node",
            capabilities=["intent_processing", "action_execution"],
            cost_weight=0.8,
            latency_weight=0.9,
            confidence_weight=0.95
        )
        
        assert fingerprint.node_id == "test-node"
        assert len(fingerprint.capabilities) == 2
        assert fingerprint.cost_weight == 0.8

