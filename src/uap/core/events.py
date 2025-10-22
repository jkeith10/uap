"""Event System for UAP"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ConfigDict
from ..logging_config import core_logger


class EventType(str, Enum):
    """Types of events in the UAP system"""
    INTENT_CREATED = "intent.created"
    INTENT_PROCESSED = "intent.processed"
    INTENT_FAILED = "intent.failed"
    ACTION_GRAPH_CREATED = "action_graph.created"
    ACTION_GRAPH_STARTED = "action_graph.started"
    ACTION_GRAPH_COMPLETED = "action_graph.completed"
    ACTION_GRAPH_FAILED = "action_graph.failed"
    NODE_REGISTERED = "node.registered"
    NODE_UNREGISTERED = "node.unregistered"
    MEMORY_CREATED = "memory.created"
    MEMORY_UPDATED = "memory.updated"
    REFLECTION_CREATED = "reflection.created"
    STATE_CHANGED = "state.changed"
    ROUTING_UPDATED = "routing.updated"
    ERROR_OCCURRED = "error.occurred"


@dataclass
class Event:
    """Event structure"""
    type: EventType
    source: str
    id: UUID = field(default_factory=uuid4)
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = field(default=None)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "id": str(self.id),
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary"""
        return cls(
            id=UUID(data["id"]),
            type=EventType(data["type"]),
            source=data["source"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {})
        )


class EventHook(BaseModel):
    """Event hook configuration"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "hook-001",
                "name": "HVAC Optimization Hook",
                "event_types": ["intent.created", "intent.processed"],
                "filters": {
                    "source": "hvac.*",
                    "data.domain": "hvac"
                },
                "webhook_url": "https://api.example.com/webhooks/uap",
                "is_active": True,
                "retry_count": 3,
                "timeout": 30
            }
        }
    )
    
    id: str = Field(description="Unique hook identifier")
    name: str = Field(description="Human-readable hook name")
    event_types: List[EventType] = Field(description="Event types to listen for")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Event filters")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for HTTP callbacks")
    callback_function: Optional[str] = Field(None, description="Internal callback function name")
    is_active: bool = Field(default=True, description="Whether the hook is active")
    retry_count: int = Field(default=3, description="Number of retries on failure")
    timeout: int = Field(default=30, description="Timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def matches_event(self, event: Event) -> bool:
        """Check if this hook matches an event"""
        # Check event type
        if event.type not in self.event_types:
            return False
        
        # Check filters
        for filter_key, filter_value in self.filters.items():
            if not self._check_filter(event, filter_key, filter_value):
                return False
        
        return True
    
    def _check_filter(self, event: Event, filter_key: str, filter_value: Any) -> bool:
        """Check if an event matches a specific filter"""
        # Handle nested keys (e.g., "data.domain")
        if "." in filter_key:
            keys = filter_key.split(".")
            value = event.data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return False
        else:
            # Handle top-level keys
            if filter_key == "source":
                value = event.source
            elif filter_key == "type":
                value = event.type.value
            elif filter_key == "correlation_id":
                value = event.correlation_id
            else:
                return False
        
        # Check if value matches filter
        if isinstance(filter_value, str) and "*" in filter_value:
            # Wildcard matching
            import fnmatch
            return fnmatch.fnmatch(str(value), filter_value)
        else:
            return value == filter_value


class EventSystem:
    """Event system for UAP with pub/sub and webhook support"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._hooks: Dict[str, EventHook] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start the event system"""
        if self._processing_task is None:
            self._processing_task = asyncio.create_task(self._process_events())
    
    async def stop(self) -> None:
        """Stop the event system"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
    
    async def publish(self, event: Event) -> None:
        """Publish an event"""
        await self._event_queue.put(event)
    
    async def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None]
    ) -> None:
        """Subscribe to an event type"""
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    
    async def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None]
    ) -> None:
        """Unsubscribe from an event type"""
        async with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                except ValueError:
                    pass
    
    async def register_hook(self, hook: EventHook) -> None:
        """Register an event hook"""
        async with self._lock:
            self._hooks[hook.id] = hook
    
    async def unregister_hook(self, hook_id: str) -> None:
        """Unregister an event hook"""
        async with self._lock:
            self._hooks.pop(hook_id, None)
    
    async def get_hooks(self) -> List[EventHook]:
        """Get all registered hooks"""
        return list(self._hooks.values())
    
    async def get_hook(self, hook_id: str) -> Optional[EventHook]:
        """Get a specific hook"""
        return self._hooks.get(hook_id)
    
    async def _process_events(self) -> None:
        """Process events from the queue"""
        while True:
            try:
                event = await self._event_queue.get()
                await self._handle_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error and continue
                core_logger.error("Event processing error", error=str(e), exc_info=True)
    
    async def _handle_event(self, event: Event) -> None:
        """Handle a single event"""
        # Notify subscribers
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    core_logger.error("Subscriber callback error", error=str(e), exc_info=True)
        
        # Process hooks
        for hook in self._hooks.values():
            if hook.is_active and hook.matches_event(event):
                asyncio.create_task(self._execute_hook(hook, event))
    
    async def _execute_hook(self, hook: EventHook, event: Event) -> None:
        """Execute an event hook"""
        if hook.webhook_url:
            await self._execute_webhook(hook, event)
        elif hook.callback_function:
            await self._execute_callback(hook, event)
    
    async def _execute_webhook(self, hook: EventHook, event: Event) -> None:
        """Execute a webhook"""
        import httpx
        
        for attempt in range(hook.retry_count + 1):
            try:
                async with httpx.AsyncClient(timeout=hook.timeout) as client:
                    response = await client.post(
                        hook.webhook_url,
                        json=event.to_dict(),
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    return  # Success
            except Exception as e:
                if attempt == hook.retry_count:
                    core_logger.error("Webhook failed", retry_count=hook.retry_count, error=str(e), exc_info=True)
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _execute_callback(self, hook: EventHook, event: Event) -> None:
        """Execute an internal callback function"""
        # This would need to be implemented based on your callback system
        # For now, we'll just log it
        core_logger.info("Executing callback", callback_function=hook.callback_function, event_id=str(event.id))
    
    async def create_event(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Event:
        """Create and publish an event"""
        event = Event(
            type=event_type,
            source=source,
            data=data,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        
        await self.publish(event)
        return event
