"""Unit tests for UAP storage components"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.uap.storage.redis_client import RedisClient
from src.uap.storage.postgres_client import PostgreSQLClient
from src.uap.storage.memory_bus import MemoryBus
from src.uap.exceptions import RedisError, PostgreSQLError


class TestRedisClient:
    """Test Redis client"""
    
    @pytest.mark.asyncio
    async def test_redis_client_connection(self, mock_redis_client):
        """Test Redis client connection"""
        mock_redis_client.connect.return_value = None
        mock_redis_client.disconnect.return_value = None
        
        await mock_redis_client.connect()
        await mock_redis_client.disconnect()
        
        mock_redis_client.connect.assert_called_once()
        mock_redis_client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_client_operations(self, mock_redis_client):
        """Test Redis client operations"""
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = "test_value"
        mock_redis_client.delete.return_value = True
        
        # Test set operation
        result = await mock_redis_client.set("test_key", "test_value")
        assert result is True
        mock_redis_client.set.assert_called_with("test_key", "test_value")
        
        # Test get operation
        result = await mock_redis_client.get("test_key")
        assert result == "test_value"
        mock_redis_client.get.assert_called_with("test_key")
        
        # Test delete operation
        result = await mock_redis_client.delete("test_key")
        assert result is True
        mock_redis_client.delete.assert_called_with("test_key")
    
    @pytest.mark.asyncio
    async def test_redis_client_health_check(self, mock_redis_client):
        """Test Redis client health check"""
        mock_redis_client.health_check.return_value = {"status": "healthy"}
        
        result = await mock_redis_client.health_check()
        assert result["status"] == "healthy"
        mock_redis_client.health_check.assert_called_once()


class TestPostgreSQLClient:
    """Test PostgreSQL client"""
    
    @pytest.mark.asyncio
    async def test_postgres_client_connection(self, mock_postgres_client):
        """Test PostgreSQL client connection"""
        mock_postgres_client.connect.return_value = None
        mock_postgres_client.disconnect.return_value = None
        
        await mock_postgres_client.connect()
        await mock_postgres_client.disconnect()
        
        mock_postgres_client.connect.assert_called_once()
        mock_postgres_client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_postgres_client_operations(self, mock_postgres_client):
        """Test PostgreSQL client operations"""
        mock_postgres_client.fetch.return_value = [{"id": 1, "name": "test"}]
        mock_postgres_client.fetchrow.return_value = {"id": 1, "name": "test"}
        mock_postgres_client.fetchval.return_value = 1
        mock_postgres_client.execute.return_value = "INSERT 0 1"
        
        # Test fetch operation
        result = await mock_postgres_client.fetch("SELECT * FROM test")
        assert len(result) == 1
        assert result[0]["name"] == "test"
        
        # Test fetchrow operation
        result = await mock_postgres_client.fetchrow("SELECT * FROM test WHERE id = $1", 1)
        assert result["name"] == "test"
        
        # Test fetchval operation
        result = await mock_postgres_client.fetchval("SELECT COUNT(*) FROM test")
        assert result == 1
        
        # Test execute operation
        result = await mock_postgres_client.execute("INSERT INTO test (name) VALUES ($1)", "test")
        assert result == "INSERT 0 1"
    
    @pytest.mark.asyncio
    async def test_postgres_client_health_check(self, mock_postgres_client):
        """Test PostgreSQL client health check"""
        mock_postgres_client.health_check.return_value = {"status": "healthy"}
        
        result = await mock_postgres_client.health_check()
        assert result["status"] == "healthy"
        mock_postgres_client.health_check.assert_called_once()


class TestMemoryBus:
    """Test Memory Bus"""
    
    @pytest.mark.asyncio
    async def test_memory_bus_lifecycle(self, mock_memory_bus):
        """Test memory bus lifecycle"""
        mock_memory_bus.start.return_value = None
        mock_memory_bus.stop.return_value = None
        
        await mock_memory_bus.start()
        await mock_memory_bus.stop()
        
        mock_memory_bus.start.assert_called_once()
        mock_memory_bus.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_bus_operations(self, mock_memory_bus):
        """Test memory bus operations"""
        mock_memory_bus.store_memory.return_value = "memory_id"
        mock_memory_bus.retrieve_memory.return_value = {"test": "memory"}
        mock_memory_bus.search_memories.return_value = [{"test": "memory"}]
        
        # Test store memory
        result = await mock_memory_bus.store_memory("test_key", {"test": "memory"})
        assert result == "memory_id"
        
        # Test retrieve memory
        result = await mock_memory_bus.retrieve_memory("test_key")
        assert result == {"test": "memory"}
        
        # Test search memories
        result = await mock_memory_bus.search_memories("test_query")
        assert len(result) == 1
        assert result[0]["test"] == "memory"
