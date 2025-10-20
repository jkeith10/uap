"""Self-Routing Intelligence for UAP"""

import asyncio
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from .packets import UAPContextPacket, PacketType
from ..storage.postgres_client import PostgreSQLClient


class NodeStatus(str, Enum):
    """Node status"""
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


@dataclass
class CapabilityFingerprint:
    """Capability fingerprint for a node"""
    node_id: str
    capabilities: List[str]
    cost_weight: float = 1.0
    latency_weight: float = 1.0
    confidence_weight: float = 1.0
    performance_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.performance_history is None:
            self.performance_history = []


@dataclass
class RoutingScore:
    """Routing score for a node"""
    node_id: str
    score: float
    cost_score: float
    latency_score: float
    confidence_score: float
    performance_score: float
    timestamp: datetime


class SelfRoutingEngine:
    """Self-routing intelligence engine"""
    
    def __init__(self, postgres_client: PostgreSQLClient):
        self.postgres = postgres_client
        self._node_fingerprints: Dict[str, CapabilityFingerprint] = {}
        self._routing_cache: Dict[str, List[RoutingScore]] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._lock = asyncio.Lock()
    
    async def register_node(
        self,
        node_id: str,
        name: str,
        capabilities: List[str],
        cost_weight: float = 1.0,
        latency_weight: float = 1.0,
        confidence_weight: float = 1.0
    ) -> None:
        """Register a node with its capabilities"""
        async with self._lock:
            fingerprint = CapabilityFingerprint(
                node_id=node_id,
                capabilities=capabilities,
                cost_weight=cost_weight,
                latency_weight=latency_weight,
                confidence_weight=confidence_weight
            )
            
            self._node_fingerprints[node_id] = fingerprint
            
            # Store in PostgreSQL
            await self.postgres.register_node_capability(
                node_id=node_id,
                name=name,
                capabilities={"capabilities": capabilities},
                fingerprint={"fingerprint": fingerprint.__dict__},
                cost_weight=cost_weight,
                latency_weight=latency_weight,
                confidence_weight=confidence_weight
            )
    
    async def unregister_node(self, node_id: str) -> None:
        """Unregister a node"""
        async with self._lock:
            self._node_fingerprints.pop(node_id, None)
            self._routing_cache.pop(node_id, None)
    
    async def route_packet(self, packet: UAPContextPacket) -> str:
        """Route a packet to the best available node"""
        # Get candidate nodes
        candidates = await self._get_candidate_nodes(packet)
        
        if not candidates:
            raise ValueError("No suitable nodes available for routing")
        
        # Calculate routing scores
        scores = []
        for node_id in candidates:
            score = await self._calculate_routing_score(packet, node_id)
            scores.append(score)
        
        # Sort by score (highest first)
        scores.sort(key=lambda x: x.score, reverse=True)
        
        # Return the best node
        return scores[0].node_id
    
    async def _get_candidate_nodes(self, packet: UAPContextPacket) -> List[str]:
        """Get candidate nodes for a packet"""
        candidates = []
        
        for node_id, fingerprint in self._node_fingerprints.items():
            # Check if node has required capabilities
            if self._node_has_capabilities(fingerprint, packet):
                candidates.append(node_id)
        
        return candidates
    
    def _node_has_capabilities(
        self,
        fingerprint: CapabilityFingerprint,
        packet: UAPContextPacket
    ) -> bool:
        """Check if a node has the required capabilities for a packet"""
        # Extract required capabilities from packet
        required_capabilities = self._extract_required_capabilities(packet)
        
        # Check if node has all required capabilities
        return all(
            capability in fingerprint.capabilities
            for capability in required_capabilities
        )
    
    def _extract_required_capabilities(self, packet: UAPContextPacket) -> List[str]:
        """Extract required capabilities from a packet"""
        capabilities = []
        
        # Extract from packet type
        if packet.type == PacketType.INTENT:
            capabilities.append("intent_processing")
        elif packet.type == PacketType.ACTION:
            capabilities.append("action_execution")
        elif packet.type == PacketType.RESULT:
            capabilities.append("result_processing")
        
        # Extract from payload
        payload = packet.payload
        if "intent" in payload:
            intent = payload["intent"]
            if "type" in intent:
                capabilities.append(f"intent_{intent['type']}")
        
        # Extract from metadata
        metadata = packet.metadata
        if "domain" in metadata:
            capabilities.append(f"domain_{metadata['domain']}")
        
        return capabilities
    
    async def _calculate_routing_score(
        self,
        packet: UAPContextPacket,
        node_id: str
    ) -> RoutingScore:
        """Calculate routing score for a node"""
        fingerprint = self._node_fingerprints[node_id]
        
        # Calculate individual scores
        cost_score = self._calculate_cost_score(fingerprint)
        latency_score = await self._calculate_latency_score(node_id)
        confidence_score = self._calculate_confidence_score(fingerprint)
        performance_score = await self._calculate_performance_score(node_id)
        
        # Calculate weighted total score
        total_score = (
            cost_score * fingerprint.cost_weight +
            latency_score * fingerprint.latency_weight +
            confidence_score * fingerprint.confidence_weight +
            performance_score * 0.5  # Performance weight
        ) / (fingerprint.cost_weight + fingerprint.latency_weight + fingerprint.confidence_weight + 0.5)
        
        return RoutingScore(
            node_id=node_id,
            score=total_score,
            cost_score=cost_score,
            latency_score=latency_score,
            confidence_score=confidence_score,
            performance_score=performance_score,
            timestamp=datetime.now(timezone.utc)
        )
    
    def _calculate_cost_score(self, fingerprint: CapabilityFingerprint) -> float:
        """Calculate cost score (lower cost = higher score)"""
        # In a real implementation, this would consider actual costs
        # For now, return a normalized score based on cost weight
        return 1.0 / fingerprint.cost_weight
    
    async def _calculate_latency_score(self, node_id: str) -> float:
        """Calculate latency score (lower latency = higher score)"""
        # In a real implementation, this would measure actual latency
        # For now, return a default score
        return 0.8
    
    def _calculate_confidence_score(self, fingerprint: CapabilityFingerprint) -> float:
        """Calculate confidence score"""
        # In a real implementation, this would consider historical performance
        # For now, return a normalized score based on confidence weight
        return 1.0 / fingerprint.confidence_weight
    
    async def _calculate_performance_score(self, node_id: str) -> float:
        """Calculate performance score based on historical data"""
        # Get performance history from PostgreSQL
        try:
            node_data = await self.postgres.get_node_capabilities(node_id)
            if node_data:
                performance_history = node_data[0].get("performance_history", [])
                
                if performance_history:
                    # Calculate average performance
                    total_score = sum(entry.get("score", 0) for entry in performance_history)
                    return total_score / len(performance_history)
            
            return 0.5  # Default score
        except Exception:
            return 0.5  # Default score on error
    
    async def update_node_performance(
        self,
        node_id: str,
        performance_data: Dict[str, Any]
    ) -> None:
        """Update node performance data"""
        async with self._lock:
            if node_id in self._node_fingerprints:
                fingerprint = self._node_fingerprints[node_id]
                fingerprint.performance_history.append(performance_data)
                
                # Keep only recent history (last 100 entries)
                if len(fingerprint.performance_history) > 100:
                    fingerprint.performance_history = fingerprint.performance_history[-100:]
                
                # Update in PostgreSQL
                await self.postgres.execute(
                    "UPDATE uap.node_capabilities SET performance_history = $1 WHERE node_id = $2",
                    fingerprint.performance_history,
                    node_id
                )
    
    async def get_available_nodes(self) -> List[str]:
        """Get list of available nodes"""
        return list(self._node_fingerprints.keys())
    
    async def get_node_capabilities(self, node_id: str) -> Optional[CapabilityFingerprint]:
        """Get capabilities for a specific node"""
        return self._node_fingerprints.get(node_id)
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "total_nodes": len(self._node_fingerprints),
            "active_nodes": len([n for n in self._node_fingerprints.values()]),
            "routing_cache_size": len(self._routing_cache),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
