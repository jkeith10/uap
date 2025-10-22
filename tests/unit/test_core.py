"""Unit tests for UAP core components"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.uap.core.kernel import WorldStateManager, WorldStateEntry
from src.uap.core.events import EventSystem, Event, EventType, EventHook
from src.uap.core.versioning import SemanticVersion, VersionManager, VersionedObject, VersionType
from src.uap.core.schema import UAPContext, UAPSchemaValidator


class TestSemanticVersion:
    """Test semantic versioning"""
    
    def test_parse_version(self):
        """Test parsing semantic version strings"""
        version = SemanticVersion.parse("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease is None
    
    def test_parse_prerelease(self):
        """Test parsing prerelease versions"""
        version = SemanticVersion.parse("1.2.3-alpha.1")
        assert version.major == 1
        assert version.prerelease == "alpha.1"
    
    def test_version_comparison(self):
        """Test version comparison"""
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("1.1.0")
        v3 = SemanticVersion.parse("2.0.0")
        
        assert v1 < v2
        assert v2 < v3
        assert v1 < v3
    
    def test_version_compatibility(self):
        """Test version compatibility"""
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("1.1.0")
        v3 = SemanticVersion.parse("2.0.0")
        
        assert v1.is_compatible_with(v2)
        assert not v1.is_compatible_with(v3)
    
    def test_next_versions(self):
        """Test version increments"""
        v = SemanticVersion.parse("1.2.3")
        
        assert str(v.next_major()) == "2.0.0"
        assert str(v.next_minor()) == "1.3.0"
        assert str(v.next_patch()) == "1.2.4"


class TestVersionManager:
    """Test version manager"""
    
    def test_register_version(self):
        """Test registering versions"""
        manager = VersionManager()
        
        obj = VersionedObject(
            id="test-obj",
            type=VersionType.PROMPT,
            version="1.0.0",
            content="Test content"
        )
        
        manager.register_version(obj)
        
        latest = manager.get_latest_version("test-obj")
        assert latest is not None
        assert latest.version == "1.0.0"
    
    def test_suggest_next_version(self):
        """Test version suggestion"""
        manager = VersionManager()
        
        # No versions yet
        assert manager.suggest_next_version("test-obj") == "1.0.0"
        
        # Add version
        obj = VersionedObject(
            id="test-obj",
            type=VersionType.PROMPT,
            version="1.0.0",
            content="Test"
        )
        manager.register_version(obj)
        
        assert manager.suggest_next_version("test-obj", "patch") == "1.0.1"
        assert manager.suggest_next_version("test-obj", "minor") == "1.1.0"
        assert manager.suggest_next_version("test-obj", "major") == "2.0.0"


class TestEventSystem:
    """Test event system"""
    
    @pytest.mark.asyncio
    async def test_event_creation(self):
        """Test creating events"""
        event_system = EventSystem()
        await event_system.start()
        
        event = await event_system.create_event(
            event_type=EventType.INTENT_CREATED,
            source="test",
            data={"test": "data"}
        )
        
        assert event.type == EventType.INTENT_CREATED
        assert event.source == "test"
        assert event.data["test"] == "data"
        
        await event_system.stop()
    
    @pytest.mark.asyncio
    async def test_event_subscription(self):
        """Test event subscription"""
        event_system = EventSystem()
        await event_system.start()
        
        callback_called = False
        received_event = None
        
        async def callback(event):
            nonlocal callback_called, received_event
            callback_called = True
            received_event = event
        
        await event_system.subscribe(EventType.INTENT_CREATED, callback)
        
        await event_system.create_event(
            event_type=EventType.INTENT_CREATED,
            source="test",
            data={"test": "data"}
        )
        
        # Give event time to be processed
        import asyncio
        await asyncio.sleep(0.1)
        
        assert callback_called
        assert received_event is not None
        
        await event_system.stop()
    
    @pytest.mark.asyncio
    async def test_event_hook(self):
        """Test event hooks"""
        event_system = EventSystem()
        await event_system.start()
        
        hook = EventHook(
            id="test-hook",
            name="Test Hook",
            event_types=[EventType.INTENT_CREATED],
            filters={"source": "test"},
            webhook_url=None,
            is_active=True
        )
        
        await event_system.register_hook(hook)
        
        hooks = await event_system.get_hooks()
        assert len(hooks) == 1
        assert hooks[0].id == "test-hook"
        
        await event_system.stop()


class TestUAPSchemaValidator:
    """Test UAP schema validation"""
    
    def test_validate_intent_packet(self):
        """Test intent packet validation"""
        valid_intent = {
            "@type": "uap:IntentPacket",
            "uap:type": "uap:optimize",
            "uap:goal": "Test goal",
            "uap:priority": 0.8,
            "uap:createdAt": "2024-01-01T00:00:00Z"
        }
        
        errors = UAPSchemaValidator.validate_intent_packet(valid_intent)
        assert len(errors) == 0
    
    def test_validate_invalid_intent(self):
        """Test validation of invalid intent"""
        invalid_intent = {
            "@type": "uap:IntentPacket",
            # Missing required fields
        }
        
        errors = UAPSchemaValidator.validate_intent_packet(invalid_intent)
        assert len(errors) > 0
    
    def test_validate_memory_stream(self):
        """Test memory stream validation"""
        valid_memory = {
            "@type": "uap:MemoryStream",
            "uap:streamId": "test-stream",
            "uap:actor": "test-actor",
            "uap:intent": {},
            "uap:granularity": "uap:task",
            "uap:retentionPolicy": "uap:permanent",
            "uap:createdAt": "2024-01-01T00:00:00Z"
        }
        
        errors = UAPSchemaValidator.validate_memory_stream(valid_memory)
        assert len(errors) == 0

