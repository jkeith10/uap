# UAP Documentation

## Overview

The Unified Autonomy Protocol (UAP) is a cross-domain, self-optimizing protocol for intelligent system orchestration. It provides a unified framework for context continuity, reflexive optimization, and modular adapters across all three layers of intelligent system orchestration.

## Architecture

### Layer 1: Contextual Kernel
- **World State Manager**: Manages persistent "world state" across sessions
- **Semantic Versioning**: Standardizes schemas (JSON-LD, GraphQL)
- **Event System**: Handles event hooks for state transitions

### Layer 2: Adaptive Mediation Layer (AML)
- **Protocol Normalization**: Converts protocol-specific payloads
- **Self-Routing Intelligence**: Auto-binding adapters (Drivers, Delegates)
- **Communication Patterns**: Intent Packet, Action Graph, Memory Stream, Reflection Report

### Layer 3: Reflexion Loop
- **Memory Engine**: Built-in memory and reflection engine
- **Decision Auditor**: Evaluates task outcomes and audits decisions
- **Auto-Optimizer**: Dynamically rewrites routing logic and enables auto-tuning

## Key Features

### Self-Routing Intelligence
- Automatic protocol detection and routing
- Dynamic adapter binding
- Performance-based optimization

### Cross-Session Memory Bus
- Persistent memory across sessions
- Context continuity
- Learning from past interactions

### Universal Reflection Schema
- Standardized evaluation metrics
- Outcome scoring and feedback
- Continuous improvement

### Protocol Interoperability
- MCP (Model Context Protocol) support
- A2A (Agent-to-Agent) support
- ACP (Agent Communication Protocol) support

## Installation

```bash
# Install dependencies
poetry install

# Start services
docker-compose up -d

# Run tests
pytest

# Start the service
python -m src.uap.main
```

## Configuration

UAP uses environment-based configuration. Create a `.env` file:

```env
# Environment
UAP_ENVIRONMENT=development
UAP_DEBUG=true

# Database
UAP_DATABASE__HOST=localhost
UAP_DATABASE__PORT=5432
UAP_DATABASE__NAME=uap
UAP_DATABASE__USER=uap
UAP_DATABASE__PASSWORD=password

# Redis
UAP_REDIS__HOST=localhost
UAP_REDIS__PORT=6379
UAP_REDIS__DB=0

# Logging
UAP_LOGGING__LEVEL=INFO
UAP_LOGGING__FORMAT=json
```

## Usage

### Basic Usage

```python
from src.uap import UAP

# Initialize UAP
uap = UAP()

# Create an intent
intent = IntentPacket(
    type="action",
    content="Adjust HVAC temperature to 72°F",
    context={"room": "conference_room_a"}
)

# Process intent
result = await uap.process_intent(intent)
```

### Advanced Usage

```python
from src.uap import UAP, ActionGraph, ActionNode

# Create action graph
node1 = ActionNode(type="sensor_read", data={"sensor": "temperature"})
node2 = ActionNode(type="hvac_adjust", data={"target_temp": 72})
graph = ActionGraph(nodes=[node1, node2], edges=[{"from": node1.id, "to": node2.id}])

# Execute graph
result = await uap.execute_graph(graph)
```

## API Reference

### Models

#### IntentPacket
Represents a natural language request as a structured action object.

```python
class IntentPacket(BaseModel):
    id: UUID
    type: IntentType
    content: str
    context: Dict[str, Any]
    priority: IntentPriority
    created_at: datetime
```

#### ActionGraph
Represents a task tree with nodes and edges.

```python
class ActionGraph(BaseModel):
    id: UUID
    nodes: List[ActionNode]
    edges: List[Dict[str, str]]
    status: GraphStatus
    created_at: datetime
    updated_at: datetime
```

#### MemoryStream
Append-only event log for cross-session memory.

```python
class MemoryStream(BaseModel):
    id: UUID
    granularity: MemoryGranularity
    entries: List[MemoryEntry]
    created_at: datetime
```

#### ReflectionReport
Evaluation results injected back into the loop.

```python
class ReflectionReport(BaseModel):
    id: UUID
    type: str
    evaluations: List[EvaluationResult]
    created_at: datetime
```

### Core Components

#### WorldStateManager
Manages persistent world state across sessions.

```python
class WorldStateManager:
    async def get_state(self, key: str) -> Optional[Dict[str, Any]]
    async def set_state(self, key: str, value: Dict[str, Any]) -> None
    async def delete_state(self, key: str) -> None
```

#### EventSystem
Handles event hooks for state transitions.

```python
class EventSystem:
    async def create_event(self, event_type: EventType, source: str, data: Dict[str, Any]) -> Event
    async def subscribe(self, event_type: EventType, callback: Callable) -> None
    async def unsubscribe(self, event_type: EventType, callback: Callable) -> None
```

#### MemoryBus
Unified interface for cross-session memory sharing.

```python
class MemoryBus:
    async def store_memory(self, key: str, value: Dict[str, Any]) -> str
    async def retrieve_memory(self, key: str) -> Optional[Dict[str, Any]]
    async def search_memories(self, query: str) -> List[Dict[str, Any]]
```

## Examples

### HVAC Workflow

```python
from src.uap import UAP, IntentPacket, ActionGraph, ActionNode

# Create HVAC intent
intent = IntentPacket(
    type="action",
    content="Optimize HVAC for conference room A",
    context={
        "room": "conference_room_a",
        "occupancy": 8,
        "current_temp": 75,
        "target_temp": 72
    }
)

# Create action graph
sensor_node = ActionNode(
    type="sensor_read",
    data={"sensor": "temperature", "room": "conference_room_a"}
)

hvac_node = ActionNode(
    type="hvac_adjust",
    data={"room": "conference_room_a", "target_temp": 72}
)

graph = ActionGraph(
    nodes=[sensor_node, hvac_node],
    edges=[{"from": sensor_node.id, "to": hvac_node.id}]
)

# Process workflow
uap = UAP()
result = await uap.process_intent(intent)
graph_result = await uap.execute_graph(graph)
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run e2e tests only
pytest tests/e2e/

# Run with coverage
pytest --cov=src/uap --cov-report=html
```

### Test Structure

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for component interactions
- `tests/e2e/` - End-to-end tests for complete workflows

## Deployment

### Docker

```bash
# Build image
docker build -t uap .

# Run container
docker run -p 8000:8000 uap
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uap
spec:
  replicas: 3
  selector:
    matchLabels:
      app: uap
  template:
    metadata:
      labels:
        app: uap
    spec:
      containers:
      - name: uap
        image: uap:latest
        ports:
        - containerPort: 8000
        env:
        - name: UAP_ENVIRONMENT
          value: "production"
```

## Monitoring

### Health Checks

```bash
# Health check endpoint
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics
```

### Logging

UAP uses structured logging with JSON format:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "logger": "uap.core",
  "message": "Processing intent",
  "intent_id": "123e4567-e89b-12d3-a456-426614174000",
  "intent_type": "action"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
