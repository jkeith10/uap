"""Protocol Mediator - Core of the Adaptive Mediation Layer"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .packets import UAPContextPacket, PacketType, ProtocolType
from .routing import SelfRoutingEngine
from .adapters.drivers import DriverRegistry, BaseDriver
from .adapters.delegates import DelegateRegistry, BaseDelegate


class ProtocolMediator:
    """Mediates between different protocols and normalizes communications"""
    
    def __init__(
        self,
        routing_engine: SelfRoutingEngine,
        driver_registry: DriverRegistry,
        delegate_registry: DelegateRegistry
    ):
        self.routing_engine = routing_engine
        self.driver_registry = driver_registry
        self.delegate_registry = delegate_registry
        self._processing_queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the protocol mediator"""
        if self._processing_task is None:
            self._processing_task = asyncio.create_task(self._process_packets())
    
    async def stop(self) -> None:
        """Stop the protocol mediator"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
    
    async def process_packet(
        self,
        packet: UAPContextPacket,
        target_protocol: Optional[ProtocolType] = None
    ) -> UAPContextPacket:
        """Process a UAP context packet"""
        # Determine target protocol if not specified
        if target_protocol is None:
            target_protocol = await self._determine_target_protocol(packet)
        
        # Update packet with target protocol
        packet.target_protocol = target_protocol
        
        # Route to appropriate node
        target_node = await self.routing_engine.route_packet(packet)
        packet.target_node = target_node
        
        # Convert to target protocol format
        protocol_data = packet.to_protocol_format(target_protocol)
        
        # Send via appropriate adapter
        result = await self._send_via_adapter(packet, protocol_data, target_protocol)
        
        # Convert result back to UAP format
        return UAPContextPacket.from_protocol_format(result, target_protocol)
    
    async def _determine_target_protocol(self, packet: UAPContextPacket) -> ProtocolType:
        """Determine the best target protocol for a packet"""
        # Get available nodes and their protocols
        available_nodes = await self.routing_engine.get_available_nodes()
        
        # For now, use the same protocol as source
        # In a real implementation, this would be more sophisticated
        return packet.source_protocol
    
    async def _send_via_adapter(
        self,
        packet: UAPContextPacket,
        protocol_data: Dict[str, Any],
        protocol: ProtocolType
    ) -> Dict[str, Any]:
        """Send packet via appropriate adapter"""
        if protocol in [ProtocolType.REST, ProtocolType.GRPC, ProtocolType.WEBSOCKET, ProtocolType.GRAPHQL, ProtocolType.MQTT]:
            # Use driver for API protocols
            driver = self.driver_registry.get_driver(protocol)
            if driver:
                return await driver.send(protocol_data)
            else:
                raise ValueError(f"No driver available for protocol: {protocol}")
        else:
            # Use delegate for AI model protocols
            delegate = self.delegate_registry.get_delegate(protocol)
            if delegate:
                return await delegate.send(protocol_data)
            else:
                raise ValueError(f"No delegate available for protocol: {protocol}")
    
    async def _process_packets(self) -> None:
        """Background packet processing loop"""
        while True:
            try:
                packet = await self._processing_queue.get()
                await self.process_packet(packet)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Packet processing error: {e}")
    
    async def queue_packet(self, packet: UAPContextPacket) -> None:
        """Queue a packet for processing"""
        await self._processing_queue.put(packet)
