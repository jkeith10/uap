"""GraphQL Bridge Implementation"""

from __future__ import annotations

import httpx
from typing import Any, Dict, Optional

from ..aml.packets import UAPContextPacket, PacketType, ProtocolType
from ..logging_config import get_logger
from ..exceptions import ProtocolError

logger = get_logger(__name__)


class GraphQLBridge:
    """GraphQL protocol bridge for UAP"""
    
    def __init__(self, config: Dict[str, Any]):
        self.endpoint = config.get("endpoint", "http://localhost:4000/graphql")
        self.timeout = config.get("timeout", 30)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> None:
        """Connect to GraphQL endpoint"""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        logger.info("GraphQL bridge connected", endpoint=self.endpoint)
    
    async def disconnect(self) -> None:
        """Disconnect from GraphQL endpoint"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def send_packet(self, packet: UAPContextPacket) -> UAPContextPacket:
        """Send UAP packet via GraphQL"""
        if not self._client:
            await self.connect()
        
        # Convert UAP packet to GraphQL mutation
        query, variables = self._uap_to_graphql(packet)
        
        # Send GraphQL request
        response = await self._client.post(
            self.endpoint,
            json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        
        # Convert response back to UAP packet
        return self._graphql_to_uap(response.json(), packet)
    
    def _uap_to_graphql(self, packet: UAPContextPacket) -> tuple[str, Dict[str, Any]]:
        """Convert UAP packet to GraphQL query and variables"""
        
        mutation = """
        mutation ProcessUAPPacket($input: UAPPacketInput!) {
            processPacket(input: $input) {
                id
                status
                result
            }
        }
        """
        
        variables = {
            "input": {
                "id": str(packet.id),
                "type": packet.type.value,
                "sourceNode": packet.source_node,
                "targetNode": packet.target_node,
                "payload": packet.payload,
                "metadata": packet.metadata
            }
        }
        
        return mutation, variables
    
    def _graphql_to_uap(
        self,
        response: Dict[str, Any],
        original_packet: UAPContextPacket
    ) -> UAPContextPacket:
        """Convert GraphQL response to UAP packet"""
        
        data = response.get("data", {}).get("processPacket", {})
        
        return UAPContextPacket(
            type=PacketType.RESULT,
            source_protocol=ProtocolType.GRAPHQL,
            target_protocol=original_packet.source_protocol,
            source_node=original_packet.target_node,
            target_node=original_packet.source_node,
            payload={"result": data},
            correlation_id=original_packet.correlation_id
        )

