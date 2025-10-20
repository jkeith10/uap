"""WebSocket Manager for UAP"""

import asyncio
import json
from typing import Dict, Any, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone

from ..aml.packets import UAPContextPacket, PacketType, ProtocolType


class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of connection_ids
        self.connection_topics: Dict[str, Set[str]] = {}  # connection_id -> set of topics
    
    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_topics[connection_id] = set()
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, connection_id)
    
    def disconnect(self, connection_id: str) -> None:
        """Disconnect a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from subscriptions
        if connection_id in self.connection_topics:
            topics = self.connection_topics[connection_id]
            for topic in topics:
                if topic in self.subscriptions:
                    self.subscriptions[topic].discard(connection_id)
                    if not self.subscriptions[topic]:
                        del self.subscriptions[topic]
            del self.connection_topics[connection_id]
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str) -> None:
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    async def send_to_topic(self, message: Dict[str, Any], topic: str) -> None:
        """Send a message to all subscribers of a topic"""
        if topic in self.subscriptions:
            disconnected = []
            for connection_id in self.subscriptions[topic]:
                if connection_id in self.active_connections:
                    try:
                        websocket = self.active_connections[connection_id]
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        print(f"Error sending to topic {topic}, connection {connection_id}: {e}")
                        disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected:
                self.disconnect(connection_id)
    
    async def subscribe_to_topic(self, connection_id: str, topic: str) -> None:
        """Subscribe a connection to a topic"""
        if connection_id in self.active_connections:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(connection_id)
            self.connection_topics[connection_id].add(topic)
            
            # Send confirmation
            await self.send_personal_message({
                "type": "subscription_confirmed",
                "topic": topic,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, connection_id)
    
    async def unsubscribe_from_topic(self, connection_id: str, topic: str) -> None:
        """Unsubscribe a connection from a topic"""
        if connection_id in self.connection_topics and topic in self.connection_topics[connection_id]:
            self.connection_topics[connection_id].discard(topic)
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(connection_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            
            # Send confirmation
            await self.send_personal_message({
                "type": "unsubscription_confirmed",
                "topic": topic,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, connection_id)
    
    async def handle_message(self, connection_id: str, message: str) -> None:
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                topic = data.get("topic")
                if topic:
                    await self.subscribe_to_topic(connection_id, topic)
            
            elif message_type == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    await self.unsubscribe_from_topic(connection_id, topic)
            
            elif message_type == "uap_packet":
                # Handle UAP context packet
                await self._handle_uap_packet(connection_id, data)
            
            elif message_type == "ping":
                # Respond to ping
                await self.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, connection_id)
            
            else:
                # Echo unknown message types
                await self.send_personal_message({
                    "type": "echo",
                    "original_message": data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, connection_id)
        
        except json.JSONDecodeError:
            await self.send_personal_message({
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, connection_id)
        except Exception as e:
            await self.send_personal_message({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, connection_id)
    
    async def _handle_uap_packet(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle UAP context packet"""
        try:
            # Create UAP context packet from WebSocket data
            packet_data = data.get("data", {})
            packet = UAPContextPacket(
                type=PacketType(packet_data.get("type", "intent")),
                source_protocol=ProtocolType.WEBSOCKET,
                target_protocol=ProtocolType.WEBSOCKET,
                source_node=connection_id,
                target_node=packet_data.get("target_node", "unknown"),
                payload=packet_data.get("payload", {}),
                metadata=packet_data.get("metadata", {}),
                correlation_id=packet_data.get("correlation_id")
            )
            
            # In a real implementation, this would be processed through the mediator
            # For now, we'll just echo it back
            await self.send_personal_message({
                "type": "uap_packet_response",
                "data": {
                    "packet_id": str(packet.id),
                    "status": "received",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }, connection_id)
        
        except Exception as e:
            await self.send_personal_message({
                "type": "error",
                "message": f"Error processing UAP packet: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, connection_id)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_subscription_count(self) -> int:
        """Get the total number of subscriptions"""
        return sum(len(subscribers) for subscribers in self.subscriptions.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            "active_connections": self.get_connection_count(),
            "total_subscriptions": self.get_subscription_count(),
            "topics": list(self.subscriptions.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
