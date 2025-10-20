"""Agent-to-Agent (A2A) Bridge Implementation"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone
import httpx
import websockets

from ..aml.packets import UAPContextPacket, PacketType, ProtocolType
from ..models import IntentPacket


class A2ABridge:
    """Full A2A protocol implementation for UAP"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = config.get("agent_id", "uap-agent")
        self.peer_agents = config.get("peer_agents", [])
        self.message_queue = asyncio.Queue()
        self._connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self._message_handlers: Dict[str, callable] = {}
        self._session: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> None:
        """Connect to A2A network"""
        self._session = httpx.AsyncClient(timeout=30)
        
        # Connect to peer agents
        for peer in self.peer_agents:
            await self._connect_to_peer(peer)
        
        # Start message processing loop
        asyncio.create_task(self._process_messages())
    
    async def disconnect(self) -> None:
        """Disconnect from A2A network"""
        # Close all connections
        for connection in self._connections.values():
            await connection.close()
        self._connections.clear()
        
        if self._session:
            await self._session.aclose()
            self._session = None
    
    async def send_packet(self, packet: UAPContextPacket) -> UAPContextPacket:
        """Send UAP packet via A2A protocol"""
        
        # Convert UAP packet to A2A format
        a2a_message = self._uap_to_a2a(packet)
        
        # Send to target agent
        response = await self._send_a2a_message(packet.target_node, a2a_message)
        
        # Convert A2A response back to UAP format
        return self._a2a_to_uap(response, packet)
    
    async def _connect_to_peer(self, peer_url: str) -> None:
        """Connect to a peer agent"""
        
        try:
            # Convert HTTP URL to WebSocket URL
            ws_url = peer_url.replace("http", "ws") + "/a2a/ws"
            
            # Connect to peer
            connection = await websockets.connect(ws_url)
            self._connections[peer_url] = connection
            
            # Send handshake
            handshake = {
                "type": "handshake",
                "agent_id": self.agent_id,
                "capabilities": ["uap_packet", "intent_processing", "action_execution"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await connection.send(json.dumps(handshake))
            
            # Wait for handshake response
            response = await connection.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "handshake_ack":
                print(f"Connected to peer agent: {peer_url}")
            else:
                print(f"Handshake failed with peer: {peer_url}")
                await connection.close()
                del self._connections[peer_url]
        
        except Exception as e:
            print(f"Failed to connect to peer {peer_url}: {e}")
    
    async def _send_a2a_message(self, target_agent: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send A2A message to target agent"""
        
        # Find connection to target agent
        connection = None
        for peer_url, conn in self._connections.items():
            if target_agent in peer_url:
                connection = conn
                break
        
        if not connection:
            raise Exception(f"No connection to agent: {target_agent}")
        
        # Send message
        await connection.send(json.dumps(message))
        
        # Wait for response
        response = await connection.recv()
        return json.loads(response)
    
    async def _process_messages(self) -> None:
        """Process incoming A2A messages"""
        
        while True:
            try:
                # Check all connections for messages
                for peer_url, connection in self._connections.items():
                    try:
                        # Non-blocking receive
                        message = await asyncio.wait_for(connection.recv(), timeout=0.1)
                        message_data = json.loads(message)
                        
                        # Process message
                        await self._handle_incoming_message(message_data, peer_url)
                    
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        # Connection closed, try to reconnect
                        await self._reconnect_peer(peer_url)
                
                await asyncio.sleep(0.1)
            
            except Exception as e:
                print(f"Error processing A2A messages: {e}")
                await asyncio.sleep(1)
    
    async def _handle_incoming_message(self, message: Dict[str, Any], peer_url: str) -> None:
        """Handle incoming A2A message"""
        
        message_type = message.get("type")
        
        if message_type == "uap_packet":
            # Handle UAP packet
            await self._handle_uap_packet(message, peer_url)
        
        elif message_type == "handshake_ack":
            # Handle handshake acknowledgment
            print(f"Handshake acknowledged by: {peer_url}")
        
        elif message_type == "ping":
            # Handle ping
            pong = {
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self._connections[peer_url].send(json.dumps(pong))
        
        else:
            # Unknown message type
            print(f"Unknown message type from {peer_url}: {message_type}")
    
    async def _handle_uap_packet(self, message: Dict[str, Any], peer_url: str) -> None:
        """Handle incoming UAP packet"""
        
        # Extract UAP packet data
        packet_data = message.get("content", {})
        
        # Create UAP packet
        packet = UAPContextPacket(
            id=packet_data.get("packet_id", ""),
            type=PacketType(packet_data.get("type", "intent")),
            source_protocol=ProtocolType.A2A,
            target_protocol=ProtocolType.A2A,
            source_node=message.get("sender", "unknown"),
            target_node=self.agent_id,
            payload=packet_data.get("payload", {}),
            metadata=packet_data.get("metadata", {}),
            correlation_id=packet_data.get("correlation_id")
        )
        
        # Process packet (this would be handled by the UAP system)
        # For now, we'll just acknowledge receipt
        response = {
            "type": "uap_packet_response",
            "message_id": message.get("message_id", ""),
            "status": "received",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self._connections[peer_url].send(json.dumps(response))
    
    async def _reconnect_peer(self, peer_url: str) -> None:
        """Reconnect to a peer agent"""
        
        if peer_url in self._connections:
            del self._connections[peer_url]
        
        # Wait before reconnecting
        await asyncio.sleep(5)
        
        # Try to reconnect
        await self._connect_to_peer(peer_url)
    
    def _uap_to_a2a(self, packet: UAPContextPacket) -> Dict[str, Any]:
        """Convert UAP packet to A2A format"""
        
        return {
            "type": "uap_packet",
            "message_id": f"msg-{packet.id}",
            "sender": self.agent_id,
            "recipient": packet.target_node,
            "content": {
                "packet_id": str(packet.id),
                "type": packet.type.value,
                "payload": packet.payload,
                "metadata": packet.metadata,
                "correlation_id": packet.correlation_id,
                "created_at": packet.created_at.isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _a2a_to_uap(self, a2a_response: Dict[str, Any], original_packet: UAPContextPacket) -> UAPContextPacket:
        """Convert A2A response to UAP packet"""
        
        # Create response packet
        response_packet = UAPContextPacket(
            type=PacketType.RESULT,
            source_protocol=ProtocolType.A2A,
            target_protocol=original_packet.source_protocol,
            source_node=original_packet.target_node,
            target_node=original_packet.source_node,
            payload={
                "a2a_response": a2a_response,
                "original_packet_id": str(original_packet.id)
            },
            metadata={
                "a2a_message_id": a2a_response.get("message_id", ""),
                "a2a_status": a2a_response.get("status", "")
            },
            correlation_id=original_packet.correlation_id
        )
        
        return response_packet
    
    async def broadcast_message(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Broadcast message to all connected peers"""
        
        responses = []
        
        for peer_url, connection in self._connections.items():
            try:
                await connection.send(json.dumps(message))
                response = await connection.recv()
                responses.append(json.loads(response))
            except Exception as e:
                print(f"Failed to send to {peer_url}: {e}")
        
        return responses
    
    async def discover_agents(self) -> List[Dict[str, Any]]:
        """Discover available agents in the network"""
        
        discovery_message = {
            "type": "discovery",
            "agent_id": self.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        responses = await self.broadcast_message(discovery_message)
        
        agents = []
        for response in responses:
            if response.get("type") == "discovery_response":
                agents.append({
                    "agent_id": response.get("agent_id"),
                    "capabilities": response.get("capabilities", []),
                    "status": response.get("status", "unknown")
                })
        
        return agents
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        
        try:
            start_time = datetime.now(timezone.utc)
            
            # Send ping to all peers
            ping_message = {
                "type": "ping",
                "timestamp": start_time.isoformat()
            }
            
            responses = await self.broadcast_message(ping_message)
            end_time = datetime.now(timezone.utc)
            
            return {
                "status": "healthy",
                "latency_ms": (end_time - start_time).total_seconds() * 1000,
                "connected_peers": len(self._connections),
                "ping_responses": len(responses),
                "timestamp": end_time.isoformat()
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected_peers": len(self._connections),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
