"""Streaming client for UAP WebSocket events"""

from __future__ import annotations

import json
import asyncio
from typing import Any, Callable, Dict, Optional, AsyncGenerator
from uuid import UUID

import websockets
from websockets.client import WebSocketClientProtocol

from ..logging_config import get_logger
from .exceptions import UAPClientError

logger = get_logger(__name__)


class StreamingClient:
    """WebSocket streaming client for UAP"""
    
    def __init__(
        self,
        base_url: str = "ws://localhost:8000",
        reconnect_interval: int = 5,
        max_reconnect_attempts: int = 10
    ):
        self.base_url = base_url.rstrip("/")
        self.ws_url = f"{self.base_url}/ws"
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._subscriptions: Dict[str, Callable] = {}
        self._running = False
    
    async def connect(self) -> None:
        """Connect to WebSocket"""
        try:
            self._websocket = await websockets.connect(self.ws_url)
            self._running = True
            logger.info("Streaming client connected", url=self.ws_url)
        except Exception as e:
            logger.error("Failed to connect", error=str(e))
            raise UAPClientError(f"Failed to connect: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        self._running = False
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
            logger.info("Streaming client disconnected")
    
    async def subscribe(
        self,
        topic: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Subscribe to a topic"""
        self._subscriptions[topic] = callback
        
        # Send subscription message
        if self._websocket:
            await self._websocket.send(json.dumps({
                "type": "subscribe",
                "topic": topic
            }))
            logger.info("Subscribed to topic", topic=topic)
    
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic"""
        self._subscriptions.pop(topic, None)
        
        # Send unsubscription message
        if self._websocket:
            await self._websocket.send(json.dumps({
                "type": "unsubscribe",
                "topic": topic
            }))
            logger.info("Unsubscribed from topic", topic=topic)
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message via WebSocket"""
        if not self._websocket:
            raise UAPClientError("Not connected to WebSocket")
        
        try:
            await self._websocket.send(json.dumps(message))
        except Exception as e:
            logger.error("Failed to send message", error=str(e))
            raise UAPClientError(f"Failed to send message: {e}")
    
    async def receive_messages(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Receive messages from WebSocket"""
        if not self._websocket:
            raise UAPClientError("Not connected to WebSocket")
        
        while self._running:
            try:
                message = await self._websocket.recv()
                data = json.loads(message)
                
                # Handle subscriptions
                msg_type = data.get("type")
                if msg_type in self._subscriptions:
                    callback = self._subscriptions[msg_type]
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                
                yield data
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, attempting reconnect")
                await self._reconnect()
            except Exception as e:
                logger.error("Error receiving message", error=str(e))
    
    async def _reconnect(self) -> None:
        """Attempt to reconnect to WebSocket"""
        for attempt in range(self.max_reconnect_attempts):
            try:
                await asyncio.sleep(self.reconnect_interval)
                await self.connect()
                
                # Resubscribe to topics
                for topic in self._subscriptions.keys():
                    await self._websocket.send(json.dumps({
                        "type": "subscribe",
                        "topic": topic
                    }))
                
                logger.info("Reconnected successfully")
                return
            except Exception as e:
                logger.warning(
                    "Reconnect attempt failed",
                    attempt=attempt + 1,
                    max_attempts=self.max_reconnect_attempts,
                    error=str(e)
                )
        
        raise UAPClientError("Failed to reconnect after maximum attempts")
    
    async def listen(self) -> None:
        """Listen for messages and dispatch to callbacks"""
        async for message in self.receive_messages():
            pass  # Callbacks are already handled in receive_messages
