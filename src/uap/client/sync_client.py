"""Synchronous UAP Client for Python"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..models.intent import IntentPacket
from ..models.action_graph import ActionGraph
from ..models.memory_stream import MemoryStream
from ..models.reflection import ReflectionReport
from .async_client import AsyncUAPClient
from .exceptions import UAPClientError


class UAPClient:
    """Synchronous wrapper for AsyncUAPClient"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self._async_client = AsyncUAPClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries
        )
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def __enter__(self) -> UAPClient:
        """Context manager entry"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._async_client.connect())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self._loop:
            self._loop.run_until_complete(self._async_client.disconnect())
            self._loop.close()
            self._loop = None
    
    def _run_async(self, coro):
        """Run async coroutine synchronously"""
        if not self._loop:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)
    
    # Intent operations
    def create_intent(self, intent: IntentPacket) -> IntentPacket:
        """Create a new intent"""
        return self._run_async(self._async_client.create_intent(intent))
    
    def get_intent(self, intent_id: UUID) -> IntentPacket:
        """Get an intent by ID"""
        return self._run_async(self._async_client.get_intent(intent_id))
    
    def list_intents(self, limit: int = 100, offset: int = 0) -> List[IntentPacket]:
        """List intents with pagination"""
        return self._run_async(self._async_client.list_intents(limit, offset))
    
    # Action Graph operations
    def create_action_graph(self, graph: ActionGraph) -> ActionGraph:
        """Create a new action graph"""
        return self._run_async(self._async_client.create_action_graph(graph))
    
    def get_action_graph(self, graph_id: UUID) -> ActionGraph:
        """Get an action graph by ID"""
        return self._run_async(self._async_client.get_action_graph(graph_id))
    
    def execute_action_graph(self, graph_id: UUID) -> Dict[str, Any]:
        """Execute an action graph"""
        return self._run_async(self._async_client.execute_action_graph(graph_id))
    
    # Memory Stream operations
    def create_memory_stream(self, memory: MemoryStream) -> MemoryStream:
        """Create a new memory stream"""
        return self._run_async(self._async_client.create_memory_stream(memory))
    
    def get_memory_stream(self, memory_id: UUID) -> MemoryStream:
        """Get a memory stream by ID"""
        return self._run_async(self._async_client.get_memory_stream(memory_id))
    
    def search_memories(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search memory streams"""
        return self._run_async(self._async_client.search_memories(query))
    
    # Reflection Report operations
    def create_reflection_report(self, report: ReflectionReport) -> ReflectionReport:
        """Create a new reflection report"""
        return self._run_async(self._async_client.create_reflection_report(report))
    
    def get_reflection_report(self, report_id: UUID) -> ReflectionReport:
        """Get a reflection report by ID"""
        return self._run_async(self._async_client.get_reflection_report(report_id))
    
    # Health and status operations
    def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        return self._run_async(self._async_client.health_check())
    
    def detailed_health_check(self) -> Dict[str, Any]:
        """Get detailed health check"""
        return self._run_async(self._async_client.detailed_health_check())
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        return self._run_async(self._async_client.get_metrics())
