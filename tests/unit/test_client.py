"""Unit tests for UAP client library"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from uap.client.async_client import AsyncUAPClient
from uap.client.sync_client import UAPClient
from uap.client.exceptions import UAPClientError
from uap.models.intent import IntentPacket, IntentType, IntentPriority


class TestAsyncUAPClient:
    """Test async UAP client"""
    
    @pytest.mark.asyncio
    async def test_client_connection(self):
        """Test client connection"""
        client = AsyncUAPClient("http://localhost:8000")
        
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        async with AsyncUAPClient("http://localhost:8000") as client:
            assert client._client is not None
    
    @pytest.mark.asyncio
    async def test_create_intent_error_handling(self):
        """Test error handling in create_intent"""
        client = AsyncUAPClient("http://invalid-url:9999")
        
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Test",
            context={},
            priority=IntentPriority.MEDIUM
        )
        
        with pytest.raises(UAPClientError):
            await client.create_intent(intent)


class TestSyncUAPClient:
    """Test sync UAP client"""
    
    def test_sync_client_creation(self):
        """Test creating sync client"""
        client = UAPClient("http://localhost:8000")
        
        assert client._async_client.base_url == "http://localhost:8000"

