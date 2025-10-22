"""Async UAP Client for Python"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from httpx import AsyncClient, Response

from ..models.intent import IntentPacket
from ..models.action_graph import ActionGraph
from ..models.memory_stream import MemoryStream
from ..models.reflection import ReflectionReport
from ..retry import retry_async, RetryConfig
from ..logging_config import get_logger
from .exceptions import UAPClientError

logger = get_logger(__name__)


class AsyncUAPClient:
    """Async client for UAP API"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retry_config = RetryConfig(
            max_attempts=max_retries,
            retryable_exceptions=(httpx.HTTPError,)
        )
        self._client: Optional[AsyncClient] = None
    
    async def __aenter__(self) -> AsyncUAPClient:
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect the client"""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self._client = AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers
        )
        
        logger.info("UAP client connected", base_url=self.base_url)
    
    async def disconnect(self) -> None:
        """Disconnect the client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("UAP client disconnected")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Response:
        """Make an HTTP request with retry logic"""
        if not self._client:
            await self.connect()
        
        async def make_request():
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response
        
        return await retry_async(make_request, config=self.retry_config)
    
    # Intent operations
    async def create_intent(self, intent: IntentPacket) -> IntentPacket:
        """Create a new intent"""
        try:
            response = await self._request(
                "POST",
                "/api/v1/intents",
                json=intent.model_dump(mode="json")
            )
            return IntentPacket.model_validate(response.json())
        except Exception as e:
            logger.error("Failed to create intent", error=str(e))
            raise UAPClientError(f"Failed to create intent: {e}")
    
    async def get_intent(self, intent_id: UUID) -> IntentPacket:
        """Get an intent by ID"""
        try:
            response = await self._request(
                "GET",
                f"/api/v1/intents/{intent_id}"
            )
            return IntentPacket.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise UAPClientError(f"Intent {intent_id} not found")
            raise UAPClientError(f"Failed to get intent: {e}")
    
    async def list_intents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[IntentPacket]:
        """List intents with pagination"""
        try:
            response = await self._request(
                "GET",
                "/api/v1/intents",
                params={"limit": limit, "offset": offset}
            )
            data = response.json()
            return [IntentPacket.model_validate(item) for item in data.get("items", [])]
        except Exception as e:
            logger.error("Failed to list intents", error=str(e))
            raise UAPClientError(f"Failed to list intents: {e}")
    
    # Action Graph operations
    async def create_action_graph(self, graph: ActionGraph) -> ActionGraph:
        """Create a new action graph"""
        try:
            response = await self._request(
                "POST",
                "/api/v1/graphs",
                json=graph.model_dump(mode="json")
            )
            return ActionGraph.model_validate(response.json())
        except Exception as e:
            logger.error("Failed to create action graph", error=str(e))
            raise UAPClientError(f"Failed to create action graph: {e}")
    
    async def get_action_graph(self, graph_id: UUID) -> ActionGraph:
        """Get an action graph by ID"""
        try:
            response = await self._request(
                "GET",
                f"/api/v1/graphs/{graph_id}"
            )
            return ActionGraph.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise UAPClientError(f"Action graph {graph_id} not found")
            raise UAPClientError(f"Failed to get action graph: {e}")
    
    async def execute_action_graph(self, graph_id: UUID) -> Dict[str, Any]:
        """Execute an action graph"""
        try:
            response = await self._request(
                "POST",
                f"/api/v1/graphs/{graph_id}/execute"
            )
            return response.json()
        except Exception as e:
            logger.error("Failed to execute action graph", error=str(e))
            raise UAPClientError(f"Failed to execute action graph: {e}")
    
    # Memory Stream operations
    async def create_memory_stream(self, memory: MemoryStream) -> MemoryStream:
        """Create a new memory stream"""
        try:
            response = await self._request(
                "POST",
                "/api/v1/memories",
                json=memory.model_dump(mode="json")
            )
            return MemoryStream.model_validate(response.json())
        except Exception as e:
            logger.error("Failed to create memory stream", error=str(e))
            raise UAPClientError(f"Failed to create memory stream: {e}")
    
    async def get_memory_stream(self, memory_id: UUID) -> MemoryStream:
        """Get a memory stream by ID"""
        try:
            response = await self._request(
                "GET",
                f"/api/v1/memories/{memory_id}"
            )
            return MemoryStream.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise UAPClientError(f"Memory stream {memory_id} not found")
            raise UAPClientError(f"Failed to get memory stream: {e}")
    
    async def search_memories(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search memory streams"""
        try:
            response = await self._request(
                "POST",
                "/api/v1/memories/search",
                json=query
            )
            return response.json()
        except Exception as e:
            logger.error("Failed to search memories", error=str(e))
            raise UAPClientError(f"Failed to search memories: {e}")
    
    # Reflection Report operations
    async def create_reflection_report(self, report: ReflectionReport) -> ReflectionReport:
        """Create a new reflection report"""
        try:
            response = await self._request(
                "POST",
                "/api/v1/reflections",
                json=report.model_dump(mode="json")
            )
            return ReflectionReport.model_validate(response.json())
        except Exception as e:
            logger.error("Failed to create reflection report", error=str(e))
            raise UAPClientError(f"Failed to create reflection report: {e}")
    
    async def get_reflection_report(self, report_id: UUID) -> ReflectionReport:
        """Get a reflection report by ID"""
        try:
            response = await self._request(
                "GET",
                f"/api/v1/reflections/{report_id}"
            )
            return ReflectionReport.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise UAPClientError(f"Reflection report {report_id} not found")
            raise UAPClientError(f"Failed to get reflection report: {e}")
    
    # Health and status operations
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        try:
            response = await self._request("GET", "/health")
            return response.json()
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            raise UAPClientError(f"Health check failed: {e}")
    
    async def detailed_health_check(self) -> Dict[str, Any]:
        """Get detailed health check"""
        try:
            response = await self._request("GET", "/health/detailed")
            return response.json()
        except Exception as e:
            logger.error("Detailed health check failed", error=str(e))
            raise UAPClientError(f"Detailed health check failed: {e}")
    
    async def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        try:
            response = await self._request("GET", "/metrics")
            return response.text
        except Exception as e:
            logger.error("Failed to get metrics", error=str(e))
            raise UAPClientError(f"Failed to get metrics: {e}")
