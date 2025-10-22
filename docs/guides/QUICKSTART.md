# UAP Quickstart Guide

Welcome to the Unified Autonomy Protocol (UAP)! This guide will get you up and running in 10 minutes.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git

## Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/jkeith10/uap.git
cd uap

# Install dependencies
pip install poetry
poetry install

# Or install globally
pip install uap
```

## Step 2: Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Run database migrations
uap migrate
```

## Step 3: Start UAP Server

```bash
# Start the server
uap serve

# Or with auto-reload for development
uap serve --reload
```

The server will start at **http://localhost:8000**

## Step 4: Explore the API

### Using the Web UI

Open your browser to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

### Using the Python SDK

```python
import asyncio
from uap.client import AsyncUAPClient
from uap.models.intent import IntentPacket, IntentType, IntentPriority

async def main():
    # Create client
    async with AsyncUAPClient("http://localhost:8000") as client:
        # Create an intent
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Optimize HVAC for conference room",
            context={"room": "conference_a", "target_temp": 72},
            priority=IntentPriority.HIGH
        )
        
        # Submit intent
        result = await client.create_intent(intent)
        print(f"Intent created: {result.id}")
        
        # Get intent back
        retrieved = await client.get_intent(result.id)
        print(f"Intent retrieved: {retrieved.content}")

asyncio.run(main())
```

### Using the Synchronous Client

```python
from uap.client import UAPClient
from uap.models.intent import IntentPacket, IntentType, IntentPriority

# Create client
with UAPClient("http://localhost:8000") as client:
    # Create an intent
    intent = IntentPacket(
        type=IntentType.ACTION,
        content="Optimize HVAC for conference room",
        context={"room": "conference_a"},
        priority=IntentPriority.HIGH
    )
    
    # Submit intent
    result = client.create_intent(intent)
    print(f"Intent created: {result.id}")
```

### Using cURL

```bash
# Create an intent
curl -X POST http://localhost:8000/api/v1/intents \
  -H "Content-Type: application/json" \
  -d '{
    "type": "action",
    "content": "Optimize HVAC system",
    "context": {"room": "conference_a"},
    "priority": 1
  }'

# Check health
curl http://localhost:8000/health
```

## Step 5: Create an Action Graph

```python
from uap.client import AsyncUAPClient
from uap.models.action_graph import ActionGraph, ActionNode

async with AsyncUAPClient() as client:
    # Create action graph
    node1 = ActionNode(type="sensor_read", data={"sensor": "temperature"})
    node2 = ActionNode(type="hvac_adjust", data={"target": 72})
    
    graph = ActionGraph(
        nodes=[node1, node2],
        edges=[{"from": str(node1.id), "to": str(node2.id)}]
    )
    
    # Submit graph
    result = await client.create_action_graph(graph)
    print(f"Graph created: {result.id}")
    
    # Execute graph
    execution = await client.execute_action_graph(result.id)
    print(f"Execution status: {execution['status']}")
```

## Step 6: Use WebSocket Streaming

```python
from uap.client import StreamingClient

async def on_event(message):
    print(f"Received: {message}")

async with StreamingClient("ws://localhost:8000") as stream:
    # Subscribe to topics
    await stream.subscribe("intents.created", on_event)
    await stream.subscribe("graphs.executed", on_event)
    
    # Listen for events
    await stream.listen()
```

## Step 7: Try the CLI

```bash
# Initialize a new project
uap init my-uap-project

# Check system status
uap status

# Run a demo
uap demo

# View configuration
uap config --show
```

## Next Steps

Now that you have UAP running, explore:

1. **[Architecture Guide](ARCHITECTURE.md)** - Understand UAP's three layers
2. **[API Reference](../API.md)** - Complete API documentation
3. **[Examples](../../examples/)** - Real-world use cases
4. **[Protocol Integration](PROTOCOL_INTEGRATION.md)** - Integrate with MCP, A2A, ACP

## Troubleshooting

### Server won't start

```bash
# Check services are running
docker-compose ps

# Check logs
docker-compose logs

# Verify configuration
uap config --validate
```

### Database connection errors

```bash
# Ensure PostgreSQL is running
docker-compose up -d postgres

# Run migrations
uap migrate

# Check status
uap status
```

### Redis connection errors

```bash
# Ensure Redis is running
docker-compose up -d redis

# Check status
uap status
```

## Getting Help

- **Documentation**: https://github.com/jkeith10/uap/docs
- **Issues**: https://github.com/jkeith10/uap/issues
- **Discussions**: https://github.com/jkeith10/uap/discussions

## What's Next?

- Build your first autonomous agent
- Create custom protocol bridges
- Implement reflection-based optimization
- Deploy to production

**Welcome to UAP! 🚀**

