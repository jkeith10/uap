"""UAP Context Packet Definitions"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict


class PacketType(str, Enum):
    """Types of UAP context packets"""
    INTENT = "intent"
    ACTION = "action"
    RESULT = "result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    DISCOVERY = "discovery"


class ProtocolType(str, Enum):
    """Supported protocol types"""
    REST = "rest"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    GRAPHQL = "graphql"
    MQTT = "mqtt"
    MCP = "mcp"
    A2A = "a2a"
    ACP = "acp"


class UAPContextPacket(BaseModel):
    """Core UAP context packet for protocol normalization"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "intent",
                "source_protocol": "rest",
                "target_protocol": "mcp",
                "source_node": "api-gateway",
                "target_node": "ai-worker-1",
                "payload": {
                    "intent": {
                        "type": "optimize",
                        "goal": "optimize HVAC pricebook"
                    },
                    "context": {
                        "domain": "hvac",
                        "organization": "BellOps"
                    }
                },
                "metadata": {
                    "priority": 0.8,
                    "timeout": 30,
                    "retry_count": 3
                },
                "correlation_id": "req-001",
                "created_at": "2024-01-01T10:00:00Z"
            }
        }
    )
    
    id: UUID = Field(default_factory=uuid4, description="Unique packet identifier")
    type: PacketType = Field(description="Packet type")
    source_protocol: ProtocolType = Field(description="Source protocol type")
    target_protocol: ProtocolType = Field(description="Target protocol type")
    source_node: str = Field(description="Source node identifier")
    target_node: str = Field(description="Target node identifier")
    payload: Dict[str, Any] = Field(description="Packet payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Packet metadata")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    
    def to_protocol_format(self, protocol: ProtocolType) -> Dict[str, Any]:
        """Convert packet to specific protocol format"""
        if protocol == ProtocolType.REST:
            return self._to_rest_format()
        elif protocol == ProtocolType.GRPC:
            return self._to_grpc_format()
        elif protocol == ProtocolType.WEBSOCKET:
            return self._to_websocket_format()
        elif protocol == ProtocolType.GRAPHQL:
            return self._to_graphql_format()
        elif protocol == ProtocolType.MQTT:
            return self._to_mqtt_format()
        elif protocol == ProtocolType.MCP:
            return self._to_mcp_format()
        elif protocol == ProtocolType.A2A:
            return self._to_a2a_format()
        elif protocol == ProtocolType.ACP:
            return self._to_acp_format()
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    def _to_rest_format(self) -> Dict[str, Any]:
        """Convert to REST API format"""
        return {
            "method": "POST",
            "url": f"/uap/{self.type.value}",
            "headers": {
                "Content-Type": "application/json",
                "X-UAP-Source": self.source_node,
                "X-UAP-Target": self.target_node,
                "X-UAP-Correlation-ID": self.correlation_id or str(self.id)
            },
            "body": {
                "packet_id": str(self.id),
                "type": self.type.value,
                "payload": self.payload,
                "metadata": self.metadata,
                "created_at": self.created_at.isoformat()
            }
        }
    
    def _to_grpc_format(self) -> Dict[str, Any]:
        """Convert to gRPC format"""
        return {
            "service": "UAPService",
            "method": f"Process{self.type.value.title()}",
            "request": {
                "packet_id": str(self.id),
                "type": self.type.value,
                "source_node": self.source_node,
                "target_node": self.target_node,
                "payload": self.payload,
                "metadata": self.metadata,
                "correlation_id": self.correlation_id or str(self.id),
                "created_at": self.created_at.isoformat()
            }
        }
    
    def _to_websocket_format(self) -> Dict[str, Any]:
        """Convert to WebSocket format"""
        return {
            "type": "uap_packet",
            "data": {
                "packet_id": str(self.id),
                "type": self.type.value,
                "source_node": self.source_node,
                "target_node": self.target_node,
                "payload": self.payload,
                "metadata": self.metadata,
                "correlation_id": self.correlation_id or str(self.id),
                "created_at": self.created_at.isoformat()
            }
        }
    
    def _to_graphql_format(self) -> Dict[str, Any]:
        """Convert to GraphQL format"""
        return {
            "query": f"""
                mutation ProcessUAPPacket($input: UAPPacketInput!) {{
                    processUAPPacket(input: $input) {{
                        packetId
                        status
                        result
                    }}
                }}
            """,
            "variables": {
                "input": {
                    "packetId": str(self.id),
                    "type": self.type.value,
                    "sourceNode": self.source_node,
                    "targetNode": self.target_node,
                    "payload": self.payload,
                    "metadata": self.metadata,
                    "correlationId": self.correlation_id or str(self.id),
                    "createdAt": self.created_at.isoformat()
                }
            }
        }
    
    def _to_mqtt_format(self) -> Dict[str, Any]:
        """Convert to MQTT format"""
        topic = f"uap/{self.target_node}/{self.type.value}"
        return {
            "topic": topic,
            "payload": {
                "packet_id": str(self.id),
                "type": self.type.value,
                "source_node": self.source_node,
                "target_node": self.target_node,
                "payload": self.payload,
                "metadata": self.metadata,
                "correlation_id": self.correlation_id or str(self.id),
                "created_at": self.created_at.isoformat()
            },
            "qos": 1,
            "retain": False
        }
    
    def _to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP format"""
        return {
            "jsonrpc": "2.0",
            "id": str(self.id),
            "method": f"uap.{self.type.value}",
            "params": {
                "source_node": self.source_node,
                "target_node": self.target_node,
                "payload": self.payload,
                "metadata": self.metadata,
                "correlation_id": self.correlation_id or str(self.id),
                "created_at": self.created_at.isoformat()
            }
        }
    
    def _to_a2a_format(self) -> Dict[str, Any]:
        """Convert to A2A format"""
        return {
            "message_type": "uap_packet",
            "sender": self.source_node,
            "recipient": self.target_node,
            "content": {
                "packet_id": str(self.id),
                "type": self.type.value,
                "payload": self.payload,
                "metadata": self.metadata,
                "correlation_id": self.correlation_id or str(self.id),
                "created_at": self.created_at.isoformat()
            }
        }
    
    def _to_acp_format(self) -> Dict[str, Any]:
        """Convert to ACP format"""
        return {
            "protocol": "acp",
            "version": "1.0",
            "action": f"process_{self.type.value}",
            "agent_id": self.target_node,
            "data": {
                "packet_id": str(self.id),
                "type": self.type.value,
                "source_node": self.source_node,
                "payload": self.payload,
                "metadata": self.metadata,
                "correlation_id": self.correlation_id or str(self.id),
                "created_at": self.created_at.isoformat()
            }
        }
    
    @classmethod
    def from_protocol_format(
        cls,
        data: Dict[str, Any],
        protocol: ProtocolType
    ) -> "UAPContextPacket":
        """Create packet from specific protocol format"""
        if protocol == ProtocolType.REST:
            return cls._from_rest_format(data)
        elif protocol == ProtocolType.GRPC:
            return cls._from_grpc_format(data)
        elif protocol == ProtocolType.WEBSOCKET:
            return cls._from_websocket_format(data)
        elif protocol == ProtocolType.GRAPHQL:
            return cls._from_graphql_format(data)
        elif protocol == ProtocolType.MQTT:
            return cls._from_mqtt_format(data)
        elif protocol == ProtocolType.MCP:
            return cls._from_mcp_format(data)
        elif protocol == ProtocolType.A2A:
            return cls._from_a2a_format(data)
        elif protocol == ProtocolType.ACP:
            return cls._from_acp_format(data)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    @classmethod
    def _from_rest_format(cls, data: Dict[str, Any]) -> "UAPContextPacket":
        """Create from REST format"""
        body = data.get("body", {})
        headers = data.get("headers", {})
        
        return cls(
            id=UUID(body.get("packet_id", uuid4())),
            type=PacketType(body.get("type", "intent")),
            source_protocol=ProtocolType.REST,
            target_protocol=ProtocolType.REST,  # Will be set by mediator
            source_node=headers.get("X-UAP-Source", "unknown"),
            target_node=headers.get("X-UAP-Target", "unknown"),
            payload=body.get("payload", {}),
            metadata=body.get("metadata", {}),
            correlation_id=headers.get("X-UAP-Correlation-ID"),
            created_at=datetime.fromisoformat(body.get("created_at", datetime.now(timezone.utc).isoformat()))
        )
    
    @classmethod
    def _from_grpc_format(cls, data: Dict[str, Any]) -> "UAPContextPacket":
        """Create from gRPC format"""
        request = data.get("request", {})
        
        return cls(
            id=UUID(request.get("packet_id", uuid4())),
            type=PacketType(request.get("type", "intent")),
            source_protocol=ProtocolType.GRPC,
            target_protocol=ProtocolType.GRPC,
            source_node=request.get("source_node", "unknown"),
            target_node=request.get("target_node", "unknown"),
            payload=request.get("payload", {}),
            metadata=request.get("metadata", {}),
            correlation_id=request.get("correlation_id"),
            created_at=datetime.fromisoformat(request.get("created_at", datetime.now(timezone.utc).isoformat()))
        )
    
    @classmethod
    def _from_websocket_format(cls, data: Dict[str, Any]) -> "UAPContextPacket":
        """Create from WebSocket format"""
        ws_data = data.get("data", {})
        
        return cls(
            id=UUID(ws_data.get("packet_id", uuid4())),
            type=PacketType(ws_data.get("type", "intent")),
            source_protocol=ProtocolType.WEBSOCKET,
            target_protocol=ProtocolType.WEBSOCKET,
            source_node=ws_data.get("source_node", "unknown"),
            target_node=ws_data.get("target_node", "unknown"),
            payload=ws_data.get("payload", {}),
            metadata=ws_data.get("metadata", {}),
            correlation_id=ws_data.get("correlation_id"),
            created_at=datetime.fromisoformat(ws_data.get("created_at", datetime.now(timezone.utc).isoformat()))
        )
    
    @classmethod
    def _from_graphql_format(cls, data: Dict[str, Any]) -> "UAPContextPacket":
        """Create from GraphQL format"""
        variables = data.get("variables", {})
        input_data = variables.get("input", {})
        
        return cls(
            id=UUID(input_data.get("packetId", uuid4())),
            type=PacketType(input_data.get("type", "intent")),
            source_protocol=ProtocolType.GRAPHQL,
            target_protocol=ProtocolType.GRAPHQL,
            source_node=input_data.get("sourceNode", "unknown"),
            target_node=input_data.get("targetNode", "unknown"),
            payload=input_data.get("payload", {}),
            metadata=input_data.get("metadata", {}),
            correlation_id=input_data.get("correlationId"),
            created_at=datetime.fromisoformat(input_data.get("createdAt", datetime.now(timezone.utc).isoformat()))
        )
    
    @classmethod
    def _from_mqtt_format(cls, data: Dict[str, Any]) -> "UAPContextPacket":
        """Create from MQTT format"""
        payload = data.get("payload", {})
        topic = data.get("topic", "")
        
        # Extract target node from topic
        topic_parts = topic.split("/")
        target_node = topic_parts[2] if len(topic_parts) > 2 else "unknown"
        
        return cls(
            id=UUID(payload.get("packet_id", uuid4())),
            type=PacketType(payload.get("type", "intent")),
            source_protocol=ProtocolType.MQTT,
            target_protocol=ProtocolType.MQTT,
            source_node=payload.get("source_node", "unknown"),
            target_node=target_node,
            payload=payload.get("payload", {}),
            metadata=payload.get("metadata", {}),
            correlation_id=payload.get("correlation_id"),
            created_at=datetime.fromisoformat(payload.get("created_at", datetime.now(timezone.utc).isoformat()))
        )
    
    @classmethod
    def _from_mcp_format(cls, data: Dict[str, Any]) -> "UAPContextPacket":
        """Create from MCP format"""
        params = data.get("params", {})
        
        return cls(
            id=UUID(data.get("id", uuid4())),
            type=PacketType(params.get("type", "intent")),
            source_protocol=ProtocolType.MCP,
            target_protocol=ProtocolType.MCP,
            source_node=params.get("source_node", "unknown"),
            target_node=params.get("target_node", "unknown"),
            payload=params.get("payload", {}),
            metadata=params.get("metadata", {}),
            correlation_id=params.get("correlation_id"),
            created_at=datetime.fromisoformat(params.get("created_at", datetime.now(timezone.utc).isoformat()))
        )
    
    @classmethod
    def _from_a2a_format(cls, data: Dict[str, Any]) -> "UAPContextPacket":
        """Create from A2A format"""
        content = data.get("content", {})
        
        return cls(
            id=UUID(content.get("packet_id", uuid4())),
            type=PacketType(content.get("type", "intent")),
            source_protocol=ProtocolType.A2A,
            target_protocol=ProtocolType.A2A,
            source_node=data.get("sender", "unknown"),
            target_node=data.get("recipient", "unknown"),
            payload=content.get("payload", {}),
            metadata=content.get("metadata", {}),
            correlation_id=content.get("correlation_id"),
            created_at=datetime.fromisoformat(content.get("created_at", datetime.now(timezone.utc).isoformat()))
        )
    
    @classmethod
    def _from_acp_format(cls, data: Dict[str, Any]) -> "UAPContextPacket":
        """Create from ACP format"""
        acp_data = data.get("data", {})
        
        return cls(
            id=UUID(acp_data.get("packet_id", uuid4())),
            type=PacketType(acp_data.get("type", "intent")),
            source_protocol=ProtocolType.ACP,
            target_protocol=ProtocolType.ACP,
            source_node=acp_data.get("source_node", "unknown"),
            target_node=data.get("agent_id", "unknown"),
            payload=acp_data.get("payload", {}),
            metadata=acp_data.get("metadata", {}),
            correlation_id=acp_data.get("correlation_id"),
            created_at=datetime.fromisoformat(acp_data.get("created_at", datetime.now(timezone.utc).isoformat()))
        )
