"""Pytest configuration and fixtures"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

from src.uap.config import UAPConfig, Environment
from src.uap.storage.redis_client import RedisClient
from src.uap.storage.postgres_client import PostgreSQLClient
from src.uap.storage.memory_bus import MemoryBus
from src.uap.core.kernel import WorldStateManager
from src.uap.core.events import EventSystem


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config() -> UAPConfig:
    """Create test configuration"""
    return UAPConfig(
        environment=Environment.TESTING,
        debug=True,
        database=UAPConfig.DatabaseConfig(
            host="localhost",
            port=5432,
            name="uap_test",
            user="uap_test",
            password="test_password"
        ),
        redis=UAPConfig.RedisConfig(
            host="localhost",
            port=6379,
            db=1
        )
    )


@pytest.fixture
async def mock_redis_client() -> AsyncGenerator[AsyncMock, None]:
    """Create mock Redis client"""
    mock_client = AsyncMock(spec=RedisClient)
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
    mock_client.set = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.publish = AsyncMock()
    mock_client.subscribe = AsyncMock()
    yield mock_client


@pytest.fixture
async def mock_postgres_client() -> AsyncGenerator[AsyncMock, None]:
    """Create mock PostgreSQL client"""
    mock_client = AsyncMock(spec=PostgreSQLClient)
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
    mock_client.fetch = AsyncMock(return_value=[])
    mock_client.fetchrow = AsyncMock(return_value=None)
    mock_client.fetchval = AsyncMock(return_value=None)
    mock_client.execute = AsyncMock()
    yield mock_client


@pytest.fixture
async def mock_memory_bus() -> AsyncGenerator[AsyncMock, None]:
    """Create mock memory bus"""
    mock_bus = AsyncMock(spec=MemoryBus)
    mock_bus.start = AsyncMock()
    mock_bus.stop = AsyncMock()
    mock_bus.store_memory = AsyncMock()
    mock_bus.retrieve_memory = AsyncMock(return_value=None)
    mock_bus.search_memories = AsyncMock(return_value=[])
    yield mock_bus


@pytest.fixture
async def mock_world_state_manager() -> AsyncGenerator[AsyncMock, None]:
    """Create mock world state manager"""
    mock_manager = AsyncMock(spec=WorldStateManager)
    mock_manager.start = AsyncMock()
    mock_manager.stop = AsyncMock()
    mock_manager.get_state = AsyncMock(return_value=None)
    mock_manager.set_state = AsyncMock()
    mock_manager.delete_state = AsyncMock()
    yield mock_manager


@pytest.fixture
async def mock_event_system() -> AsyncGenerator[AsyncMock, None]:
    """Create mock event system"""
    mock_system = AsyncMock(spec=EventSystem)
    mock_system.start = AsyncMock()
    mock_system.stop = AsyncMock()
    mock_system.create_event = AsyncMock()
    mock_system.subscribe = AsyncMock()
    mock_system.unsubscribe = AsyncMock()
    yield mock_system


@pytest.fixture
def sample_intent_data() -> dict:
    """Sample intent data for testing"""
    return {
        "id": "test-intent-123",
        "type": "action",
        "content": "Test intent content",
        "context": {"test": "value"},
        "priority": 1,
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_action_graph_data() -> dict:
    """Sample action graph data for testing"""
    return {
        "id": "test-graph-123",
        "nodes": [
            {
                "id": "node-1",
                "type": "action",
                "status": "pending",
                "data": {"action": "test"}
            }
        ],
        "edges": [],
        "status": "pending",
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_memory_stream_data() -> dict:
    """Sample memory stream data for testing"""
    return {
        "id": "test-memory-123",
        "granularity": "session",
        "entries": [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "type": "event",
                "data": {"event": "test"}
            }
        ],
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_reflection_data() -> dict:
    """Sample reflection data for testing"""
    return {
        "id": "test-reflection-123",
        "type": "outcome",
        "score": 0.8,
        "feedback": {"test": "feedback"},
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_protocol_message() -> dict:
    """Sample protocol message for testing"""
    return {
        "id": "test-message-123",
        "type": "request",
        "payload": {"test": "data"},
        "timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_health_check_response() -> dict:
    """Sample health check response for testing"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "components": {
            "database": {"status": "healthy"},
            "redis": {"status": "healthy"},
            "memory_bus": {"status": "healthy"}
        }
    }
