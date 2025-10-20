"""Model Context Protocol (MCP) Bridge Implementation"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import httpx
import websockets

from ..aml.packets import UAPContextPacket, PacketType, ProtocolType
from ..models import IntentPacket


class MCPBridge:
    """Full MCP protocol implementation for UAP"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_url = config.get("server_url", "http://localhost:3000")
        self.client_id = config.get("client_id", "uap-client")
        self.timeout = config.get("timeout", 30)
        self._session: Optional[httpx.AsyncClient] = None
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._message_id = 0
    
    async def connect(self) -> None:
        """Connect to MCP server"""
        self._session = httpx.AsyncClient(
            base_url=self.server_url,
            timeout=self.timeout
        )
        
        # Initialize MCP session
        await self._initialize_session()
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server"""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        
        if self._session:
            await self._session.aclose()
            self._session = None
    
    async def send_packet(self, packet: UAPContextPacket) -> UAPContextPacket:
        """Send UAP packet via MCP protocol"""
        
        # Convert UAP packet to MCP format
        mcp_request = self._uap_to_mcp(packet)
        
        # Send via MCP
        mcp_response = await self._send_mcp_request(mcp_request)
        
        # Convert MCP response back to UAP format
        return self._mcp_to_uap(mcp_response, packet)
    
    async def _initialize_session(self) -> None:
        """Initialize MCP session"""
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "UAP Client",
                    "version": "0.1.0"
                }
            }
        }
        
        response = await self._send_mcp_request(init_request)
        
        if "error" in response:
            raise Exception(f"MCP initialization failed: {response['error']}")
    
    async def _send_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send MCP request and get response"""
        
        if not self._session:
            raise Exception("MCP bridge not connected")
        
        # Try WebSocket first, fallback to HTTP
        if self._websocket:
            return await self._send_websocket_request(request)
        else:
            return await self._send_http_request(request)
    
    async def _send_http_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send HTTP MCP request"""
        
        response = await self._session.post(
            "/mcp",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        return response.json()
    
    async def _send_websocket_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send WebSocket MCP request"""
        
        if not self._websocket:
            # Connect to WebSocket
            ws_url = self.server_url.replace("http", "ws") + "/mcp/ws"
            self._websocket = await websockets.connect(ws_url)
        
        # Send request
        await self._websocket.send(json.dumps(request))
        
        # Wait for response
        response_text = await self._websocket.recv()
        return json.loads(response_text)
    
    def _uap_to_mcp(self, packet: UAPContextPacket) -> Dict[str, Any]:
        """Convert UAP packet to MCP format"""
        
        # Map UAP packet type to MCP method
        method_map = {
            PacketType.INTENT: "tools/call",
            PacketType.ACTION: "tools/call",
            PacketType.RESULT: "notifications/tools/call_result",
            PacketType.ERROR: "notifications/error",
            PacketType.HEARTBEAT: "ping",
            PacketType.DISCOVERY: "tools/list"
        }
        
        method = method_map.get(packet.type, "tools/call")
        
        # Create MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": {
                "name": f"uap_{packet.type.value}",
                "arguments": {
                    "packet_id": str(packet.id),
                    "source_node": packet.source_node,
                    "target_node": packet.target_node,
                    "payload": packet.payload,
                    "metadata": packet.metadata,
                    "correlation_id": packet.correlation_id,
                    "created_at": packet.created_at.isoformat()
                }
            }
        }
        
        return mcp_request
    
    def _mcp_to_uap(self, mcp_response: Dict[str, Any], original_packet: UAPContextPacket) -> UAPContextPacket:
        """Convert MCP response to UAP packet"""
        
        # Extract result from MCP response
        result = mcp_response.get("result", {})
        
        # Create response packet
        response_packet = UAPContextPacket(
            type=PacketType.RESULT,
            source_protocol=ProtocolType.MCP,
            target_protocol=original_packet.source_protocol,
            source_node=original_packet.target_node,
            target_node=original_packet.source_node,
            payload={
                "mcp_response": result,
                "original_packet_id": str(original_packet.id)
            },
            metadata={
                "mcp_method": mcp_response.get("method", ""),
                "mcp_id": mcp_response.get("id", "")
            },
            correlation_id=original_packet.correlation_id
        )
        
        return response_packet
    
    def _get_next_id(self) -> str:
        """Get next message ID"""
        self._message_id += 1
        return str(self._message_id)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools"""
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list",
            "params": {}
        }
        
        response = await self._send_mcp_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to list tools: {response['error']}")
        
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool"""
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        
        response = await self._send_mcp_request(request)
        
        if "error" in response:
            raise Exception(f"Tool call failed: {response['error']}")
        
        return response.get("result", {})
    
    async def get_resources(self) -> List[Dict[str, Any]]:
        """Get available MCP resources"""
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "resources/list",
            "params": {}
        }
        
        response = await self._send_mcp_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to list resources: {response['error']}")
        
        return response.get("result", {}).get("resources", [])
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read an MCP resource"""
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "resources/read",
            "params": {
                "uri": uri
            }
        }
        
        response = await self._send_mcp_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to read resource: {response['error']}")
        
        return response.get("result", {})
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        
        try:
            start_time = datetime.now(timezone.utc)
            
            # Send ping request
            request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "ping",
                "params": {}
            }
            
            response = await self._send_mcp_request(request)
            end_time = datetime.now(timezone.utc)
            
            return {
                "status": "healthy",
                "latency_ms": (end_time - start_time).total_seconds() * 1000,
                "timestamp": end_time.isoformat(),
                "mcp_response": response
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
