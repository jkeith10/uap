"""MQTT Bridge Implementation"""

from __future__ import annotations

import json
import asyncio
from typing import Any, Callable, Dict, Optional

try:
    import aiomqtt
except ImportError:
    aiomqtt = None

from ..aml.packets import UAPContextPacket, PacketType, ProtocolType
from ..logging_config import get_logger
from ..exceptions import ProtocolError

logger = get_logger(__name__)


class MQTTBridge:
    """MQTT protocol bridge for UAP"""
    
    def __init__(self, config: Dict[str, Any]):
        if aiomqtt is None:
            raise ImportError("aiomqtt is required for MQTT bridge. Install with: pip install aiomqtt")
        
        self.broker = config.get("broker", "localhost")
        self.port = config.get("port", 1883)
        self.client_id = config.get("client_id", "uap-mqtt-client")
        self.username = config.get("username")
        self.password = config.get("password")
        self._client: Optional[aiomqtt.Client] = None
        self._subscriptions: Dict[str, Callable] = {}
    
    async def connect(self) -> None:
        """Connect to MQTT broker"""
        self._client = aiomqtt.Client(
            hostname=self.broker,
            port=self.port,
            client_id=self.client_id,
            username=self.username,
            password=self.password
        )
        await self._client.__aenter__()
        logger.info("MQTT bridge connected", broker=self.broker)
    
    async def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
    
    async def send_packet(self, packet: UAPContextPacket) -> UAPContextPacket:
        """Send UAP packet via MQTT"""
        if not self._client:
            await self.connect()
        
        # Convert UAP packet to MQTT message
        topic, payload = self._uap_to_mqtt(packet)
        
        # Publish to MQTT
        await self._client.publish(topic, json.dumps(payload), qos=1)
        
        # For simplicity, return acknowledgment packet
        return UAPContextPacket(
            type=PacketType.RESULT,
            source_protocol=ProtocolType.MQTT,
            target_protocol=packet.source_protocol,
            source_node=packet.target_node,
            target_node=packet.source_node,
            payload={"status": "published", "topic": topic},
            correlation_id=packet.correlation_id
        )
    
    async def subscribe(self, topic: str, callback: Callable) -> None:
        """Subscribe to MQTT topic"""
        if not self._client:
            await self.connect()
        
        self._subscriptions[topic] = callback
        await self._client.subscribe(topic)
        logger.info("Subscribed to MQTT topic", topic=topic)
    
    async def listen(self) -> None:
        """Listen for MQTT messages"""
        if not self._client:
            await self.connect()
        
        async for message in self._client.messages:
            topic = str(message.topic)
            
            if topic in self._subscriptions:
                payload = json.loads(message.payload.decode())
                callback = self._subscriptions[topic]
                
                if asyncio.iscoroutinefunction(callback):
                    await callback(payload)
                else:
                    callback(payload)
    
    def _uap_to_mqtt(self, packet: UAPContextPacket) -> tuple[str, Dict[str, Any]]:
        """Convert UAP packet to MQTT topic and payload"""
        
        # Create topic from target node and packet type
        topic = f"uap/{packet.target_node}/{packet.type.value}"
        
        payload = {
            "packet_id": str(packet.id),
            "source_node": packet.source_node,
            "payload": packet.payload,
            "metadata": packet.metadata,
            "correlation_id": packet.correlation_id
        }
        
        return topic, payload

