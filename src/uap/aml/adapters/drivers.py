"""API Drivers for UAP"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
import websockets
import json

from ..packets import ProtocolType


class BaseDriver(ABC):
    """Base class for API drivers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data via this driver"""
        pass
    
    @abstractmethod
    async def receive(self) -> Dict[str, Any]:
        """Receive data via this driver"""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the service"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the service"""
        pass


class RESTDriver(BaseDriver):
    """REST API driver"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8000")
        self.timeout = config.get("timeout", 30)
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> None:
        """Connect to REST API"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    async def disconnect(self) -> None:
        """Disconnect from REST API"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data via REST API"""
        if not self.client:
            await self.connect()
        
        method = data.get("method", "POST")
        url = data.get("url", "/")
        headers = data.get("headers", {})
        body = data.get("body", {})
        
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            json=body
        )
        
        response.raise_for_status()
        return response.json()
    
    async def receive(self) -> Dict[str, Any]:
        """Receive data via REST API (not applicable for REST)"""
        raise NotImplementedError("REST is request-response only")


class WebSocketDriver(BaseDriver):
    """WebSocket driver"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url", "ws://localhost:8000/ws")
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
    
    async def connect(self) -> None:
        """Connect to WebSocket"""
        self.websocket = await websockets.connect(self.url)
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data via WebSocket"""
        if not self.websocket:
            await self.connect()
        
        message = json.dumps(data)
        await self.websocket.send(message)
        
        # Wait for response
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def receive(self) -> Dict[str, Any]:
        """Receive data via WebSocket"""
        if not self.websocket:
            await self.connect()
        
        message = await self.websocket.recv()
        return json.loads(message)


class DriverRegistry:
    """Registry for API drivers"""
    
    def __init__(self):
        self._drivers: Dict[ProtocolType, BaseDriver] = {}
    
    def register_driver(self, protocol: ProtocolType, driver: BaseDriver) -> None:
        """Register a driver for a protocol"""
        self._drivers[protocol] = driver
    
    def get_driver(self, protocol: ProtocolType) -> Optional[BaseDriver]:
        """Get a driver for a protocol"""
        return self._drivers.get(protocol)
    
    def unregister_driver(self, protocol: ProtocolType) -> None:
        """Unregister a driver"""
        self._drivers.pop(protocol, None)
    
    async def connect_all(self) -> None:
        """Connect all registered drivers"""
        for driver in self._drivers.values():
            await driver.connect()
    
    async def disconnect_all(self) -> None:
        """Disconnect all registered drivers"""
        for driver in self._drivers.values():
            await driver.disconnect()
    
    def list_drivers(self) -> List[ProtocolType]:
        """List all registered drivers"""
        return list(self._drivers.keys())
