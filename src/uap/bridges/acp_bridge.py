"""Agent Communication Protocol (ACP) Bridge Implementation"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx

from ..aml.packets import UAPContextPacket, PacketType, ProtocolType
from ..models import IntentPacket


class ACPBridge:
    """Full ACP protocol implementation for UAP"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = config.get("agent_id", "uap-agent")
        self.api_endpoint = config.get("api_endpoint", "http://localhost:8080")
        self.timeout = config.get("timeout", 30)
        self._session: Optional[httpx.AsyncClient] = None
        self._request_id = 0
    
    async def connect(self) -> None:
        """Connect to ACP service"""
        self._session = httpx.AsyncClient(
            base_url=self.api_endpoint,
            timeout=self.timeout
        )
        
        # Register with ACP service
        await self._register_agent()
    
    async def disconnect(self) -> None:
        """Disconnect from ACP service"""
        if self._session:
            # Unregister agent
            await self._unregister_agent()
            await self._session.aclose()
            self._session = None
    
    async def send_packet(self, packet: UAPContextPacket) -> UAPContextPacket:
        """Send UAP packet via ACP protocol"""
        
        # Convert UAP packet to ACP format
        acp_request = self._uap_to_acp(packet)
        
        # Send via ACP
        acp_response = await self._send_acp_request(acp_request)
        
        # Convert ACP response back to UAP format
        return self._acp_to_uap(acp_response, packet)
    
    async def _register_agent(self) -> None:
        """Register agent with ACP service"""
        
        registration = {
            "protocol": "acp",
            "version": "1.0",
            "action": "register_agent",
            "agent_id": self.agent_id,
            "data": {
                "capabilities": [
                    "intent_processing",
                    "action_execution",
                    "result_processing",
                    "uap_packet_handling"
                ],
                "endpoints": {
                    "rest": f"{self.api_endpoint}/acp/{self.agent_id}",
                    "webhook": f"{self.api_endpoint}/acp/{self.agent_id}/webhook"
                },
                "metadata": {
                    "version": "0.1.0",
                    "status": "active",
                    "registered_at": datetime.now(timezone.utc).isoformat()
                }
            }
        }
        
        response = await self._send_acp_request(registration)
        
        if response.get("status") != "success":
            raise Exception(f"Agent registration failed: {response}")
    
    async def _unregister_agent(self) -> None:
        """Unregister agent from ACP service"""
        
        unregistration = {
            "protocol": "acp",
            "version": "1.0",
            "action": "unregister_agent",
            "agent_id": self.agent_id,
            "data": {
                "reason": "shutdown",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            await self._send_acp_request(unregistration)
        except Exception as e:
            print(f"Failed to unregister agent: {e}")
    
    async def _send_acp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send ACP request"""
        
        if not self._session:
            raise Exception("ACP bridge not connected")
        
        # Add request ID
        request["request_id"] = self._get_next_id()
        
        # Send request
        response = await self._session.post(
            "/acp/request",
            json=request,
            headers={
                "Content-Type": "application/json",
                "X-ACP-Agent-ID": self.agent_id
            }
        )
        
        response.raise_for_status()
        return response.json()
    
    def _uap_to_acp(self, packet: UAPContextPacket) -> Dict[str, Any]:
        """Convert UAP packet to ACP format"""
        
        # Map UAP packet type to ACP action
        action_map = {
            PacketType.INTENT: "process_intent",
            PacketType.ACTION: "execute_action",
            PacketType.RESULT: "process_result",
            PacketType.ERROR: "handle_error",
            PacketType.HEARTBEAT: "ping",
            PacketType.DISCOVERY: "discover_agents"
        }
        
        action = action_map.get(packet.type, "process_packet")
        
        return {
            "protocol": "acp",
            "version": "1.0",
            "action": action,
            "agent_id": packet.target_node,
            "data": {
                "packet_id": str(packet.id),
                "type": packet.type.value,
                "source_node": packet.source_node,
                "payload": packet.payload,
                "metadata": packet.metadata,
                "correlation_id": packet.correlation_id,
                "created_at": packet.created_at.isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _acp_to_uap(self, acp_response: Dict[str, Any], original_packet: UAPContextPacket) -> UAPContextPacket:
        """Convert ACP response to UAP packet"""
        
        # Create response packet
        response_packet = UAPContextPacket(
            type=PacketType.RESULT,
            source_protocol=ProtocolType.ACP,
            target_protocol=original_packet.source_protocol,
            source_node=original_packet.target_node,
            target_node=original_packet.source_node,
            payload={
                "acp_response": acp_response.get("data", {}),
                "original_packet_id": str(original_packet.id)
            },
            metadata={
                "acp_action": acp_response.get("action", ""),
                "acp_status": acp_response.get("status", ""),
                "acp_request_id": acp_response.get("request_id", "")
            },
            correlation_id=original_packet.correlation_id
        )
        
        return response_packet
    
    def _get_next_id(self) -> str:
        """Get next request ID"""
        self._request_id += 1
        return str(self._request_id)
    
    async def process_intent(self, intent: IntentPacket) -> Dict[str, Any]:
        """Process an intent via ACP"""
        
        acp_request = {
            "protocol": "acp",
            "version": "1.0",
            "action": "process_intent",
            "agent_id": self.agent_id,
            "data": {
                "intent": intent.dict(),
                "processing_options": {
                    "timeout": 30,
                    "retry_count": 3,
                    "priority": intent.priority
                }
            }
        }
        
        return await self._send_acp_request(acp_request)
    
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action via ACP"""
        
        acp_request = {
            "protocol": "acp",
            "version": "1.0",
            "action": "execute_action",
            "agent_id": self.agent_id,
            "data": {
                "action": action,
                "execution_options": {
                    "timeout": 60,
                    "retry_count": 2,
                    "async": True
                }
            }
        }
        
        return await self._send_acp_request(acp_request)
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of a specific agent"""
        
        acp_request = {
            "protocol": "acp",
            "version": "1.0",
            "action": "get_agent_status",
            "agent_id": agent_id,
            "data": {}
        }
        
        return await self._send_acp_request(acp_request)
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents"""
        
        acp_request = {
            "protocol": "acp",
            "version": "1.0",
            "action": "list_agents",
            "agent_id": self.agent_id,
            "data": {}
        }
        
        response = await self._send_acp_request(acp_request)
        return response.get("data", {}).get("agents", [])
    
    async def send_webhook(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook notification"""
        
        acp_request = {
            "protocol": "acp",
            "version": "1.0",
            "action": "send_webhook",
            "agent_id": self.agent_id,
            "data": {
                "webhook_url": url,
                "payload": data,
                "headers": {
                    "Content-Type": "application/json",
                    "X-ACP-Agent-ID": self.agent_id
                }
            }
        }
        
        return await self._send_acp_request(acp_request)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        
        try:
            start_time = datetime.now(timezone.utc)
            
            # Send ping request
            acp_request = {
                "protocol": "acp",
                "version": "1.0",
                "action": "ping",
                "agent_id": self.agent_id,
                "data": {}
            }
            
            response = await self._send_acp_request(acp_request)
            end_time = datetime.now(timezone.utc)
            
            return {
                "status": "healthy",
                "latency_ms": (end_time - start_time).total_seconds() * 1000,
                "timestamp": end_time.isoformat(),
                "acp_response": response
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
