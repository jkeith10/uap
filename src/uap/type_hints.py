"""Type hints and protocols for UAP"""

from __future__ import annotations

from typing import (
    Any, Dict, List, Optional, Union, TypeVar, Generic, Protocol,
    Callable, Awaitable, AsyncGenerator, Iterator, AsyncIterator,
    Set, Tuple, Mapping, Sequence, MutableMapping, MutableSequence
)
from uuid import UUID
from datetime import datetime
from enum import Enum

# Generic type variables
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')
R = TypeVar('R')

# Common type aliases
JsonDict = Dict[str, Any]
JsonList = List[Any]
JsonValue = Union[str, int, float, bool, None, JsonDict, JsonList]
Timestamp = datetime
ID = Union[str, UUID]

# Protocol definitions
class AsyncContextManager(Protocol[T]):
    async def __aenter__(self) -> T: ...
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

class StorageClient(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def health_check(self) -> Dict[str, Any]: ...

class EventHandler(Protocol):
    async def handle(self, event: Any) -> None: ...

class ProtocolBridge(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send(self, data: Any) -> Any: ...
    async def receive(self) -> Any: ...

class ReflectionEngine(Protocol):
    async def reflect(self, context: Any) -> Any: ...
    async def learn(self, outcome: Any) -> None: ...

# Model type hints
IntentData = Dict[str, Any]
ActionData = Dict[str, Any]
MemoryData = Dict[str, Any]
ReflectionData = Dict[str, Any]

# Configuration types
ConfigValue = Union[str, int, float, bool, List[str], Dict[str, Any]]
ConfigDict = Dict[str, ConfigValue]

# Event types
EventType = str
EventData = Dict[str, Any]
EventCallback = Callable[[Any], Awaitable[None]]

# Routing types
RouteDecision = Dict[str, Any]
RouteMetrics = Dict[str, float]
RouteConfig = Dict[str, Any]

# Storage types
StorageKey = str
StorageValue = Union[str, bytes, JsonDict]
StorageResult = Optional[StorageValue]

# Protocol types
ProtocolMessage = Dict[str, Any]
ProtocolResponse = Dict[str, Any]
ProtocolError = Dict[str, Any]

# Reflection types
ReflectionScore = float
ReflectionFeedback = Dict[str, Any]
ReflectionOutcome = Dict[str, Any]

# Versioning types
VersionString = str
VersionInfo = Dict[str, Any]

# Health check types
HealthStatus = str
HealthDetails = Dict[str, Any]
HealthCheck = Callable[[], Awaitable[HealthDetails]]

# Metrics types
MetricValue = Union[int, float]
MetricTags = Dict[str, str]
MetricData = Dict[str, MetricValue]

# Logging types
LogLevel = str
LogMessage = str
LogContext = Dict[str, Any]

# Async operation types
AsyncOperation = Callable[..., Awaitable[Any]]
SyncOperation = Callable[..., Any]
Operation = Union[AsyncOperation, SyncOperation]

# Error types
ErrorCode = str
ErrorDetails = Dict[str, Any]
ErrorContext = Dict[str, Any]

# Validation types
ValidationResult = Tuple[bool, Optional[str]]
Validator = Callable[[Any], ValidationResult]

# Cache types
CacheKey = str
CacheValue = Any
CacheTTL = int

# Queue types
QueueMessage = Dict[str, Any]
QueueHandler = Callable[[QueueMessage], Awaitable[None]]

# WebSocket types
WebSocketMessage = Union[str, bytes]
WebSocketHandler = Callable[[WebSocketMessage], Awaitable[None]]

# HTTP types
HTTPMethod = str
HTTPHeaders = Dict[str, str]
HTTPBody = Union[str, bytes, JsonDict]
HTTPResponse = Tuple[int, HTTPHeaders, HTTPBody]

# Database types
QueryResult = List[Dict[str, Any]]
QueryParams = Dict[str, Any]
Transaction = Any

# Redis types
RedisKey = str
RedisValue = Union[str, bytes, int, float]
RedisResult = Optional[RedisValue]

# PostgreSQL types
SQLQuery = str
SQLParams = Tuple[Any, ...]
SQLResult = List[Dict[str, Any]]

# Time types
Duration = float
Timeout = float
Interval = float

# Network types
Host = str
Port = int
URL = str
Endpoint = str

# Security types
Token = str
Secret = str
Key = str
Certificate = str

# Monitoring types
AlertLevel = str
AlertMessage = str
AlertContext = Dict[str, Any]

# Performance types
Latency = float
Throughput = float
MemoryUsage = int
CPUUsage = float

# Deployment types
Environment = str
Service = str
Instance = str
Region = str

# Feature flags
FeatureFlag = str
FeatureValue = Union[bool, str, int, float]
FeatureConfig = Dict[FeatureFlag, FeatureValue]
