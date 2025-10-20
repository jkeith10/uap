# UAP API Reference

## Overview

This document provides comprehensive API reference for the Unified Autonomy Protocol (UAP).

## REST API Endpoints

### Health Check

#### GET /health
Returns the health status of the UAP service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "components": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "memory_bus": {"status": "healthy"}
  }
}
```

### Metrics

#### GET /metrics
Returns Prometheus-formatted metrics.

**Response:**
```
# HELP uap_requests_total Total number of requests
# TYPE uap_requests_total counter
uap_requests_total{method="POST",endpoint="/intents"} 42

# HELP uap_request_duration_seconds Request duration in seconds
# TYPE uap_request_duration_seconds histogram
uap_request_duration_seconds_bucket{le="0.1"} 10
uap_request_duration_seconds_bucket{le="0.5"} 25
uap_request_duration_seconds_bucket{le="1.0"} 35
uap_request_duration_seconds_bucket{le="+Inf"} 42
```

### Intents

#### POST /intents
Create a new intent.

**Request Body:**
```json
{
  "type": "action",
  "content": "Adjust HVAC temperature to 72°F",
  "context": {
    "room": "conference_room_a",
    "current_temp": 75,
    "target_temp": 72
  },
  "priority": "high"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "action",
  "content": "Adjust HVAC temperature to 72°F",
  "context": {
    "room": "conference_room_a",
    "current_temp": 75,
    "target_temp": 72
  },
  "priority": "high",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET /intents/{intent_id}
Get an intent by ID.

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "action",
  "content": "Adjust HVAC temperature to 72°F",
  "context": {
    "room": "conference_room_a",
    "current_temp": 75,
    "target_temp": 72
  },
  "priority": "high",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Action Graphs

#### POST /action-graphs
Create a new action graph.

**Request Body:**
```json
{
  "nodes": [
    {
      "type": "sensor_read",
      "data": {
        "sensor": "temperature",
        "room": "conference_room_a"
      }
    },
    {
      "type": "hvac_adjust",
      "data": {
        "room": "conference_room_a",
        "target_temp": 72
      }
    }
  ],
  "edges": [
    {
      "from": "node-1",
      "to": "node-2"
    }
  ]
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "nodes": [
    {
      "id": "node-1",
      "type": "sensor_read",
      "data": {
        "sensor": "temperature",
        "room": "conference_room_a"
      },
      "status": "pending",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "node-2",
      "type": "hvac_adjust",
      "data": {
        "room": "conference_room_a",
        "target_temp": 72
      },
      "status": "pending",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "edges": [
    {
      "from": "node-1",
      "to": "node-2"
    }
  ],
  "status": "pending",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### GET /action-graphs/{graph_id}
Get an action graph by ID.

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "nodes": [...],
  "edges": [...],
  "status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### POST /action-graphs/{graph_id}/execute
Execute an action graph.

**Response:**
```json
{
  "graph_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "results": {
    "node-1": {
      "status": "completed",
      "result": {"temperature": 75}
    },
    "node-2": {
      "status": "completed",
      "result": {"hvac_adjusted": true}
    }
  },
  "execution_time": 1.5
}
```

### Memory Streams

#### POST /memory-streams
Create a new memory stream.

**Request Body:**
```json
{
  "granularity": "session",
  "entries": [
    {
      "type": "event",
      "data": {
        "event": "hvac_adjustment",
        "room": "conference_room_a",
        "temperature": 72
      }
    }
  ]
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "granularity": "session",
  "entries": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "type": "event",
      "data": {
        "event": "hvac_adjustment",
        "room": "conference_room_a",
        "temperature": 72
      }
    }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET /memory-streams/{stream_id}
Get a memory stream by ID.

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "granularity": "session",
  "entries": [...],
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Reflection Reports

#### POST /reflection-reports
Create a new reflection report.

**Request Body:**
```json
{
  "type": "outcome",
  "evaluations": [
    {
      "type": "outcome",
      "score": 0.9,
      "feedback": {
        "efficiency": "high",
        "accuracy": "excellent",
        "user_satisfaction": "high"
      }
    }
  ]
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "outcome",
  "evaluations": [
    {
      "type": "outcome",
      "score": 0.9,
      "feedback": {
        "efficiency": "high",
        "accuracy": "excellent",
        "user_satisfaction": "high"
      }
    }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET /reflection-reports/{report_id}
Get a reflection report by ID.

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "outcome",
  "evaluations": [...],
  "created_at": "2024-01-01T00:00:00Z"
}
```

## WebSocket API

### Connection

Connect to WebSocket endpoint:
```
ws://localhost:8000/ws
```

### Message Format

All WebSocket messages use the following format:

```json
{
  "type": "message_type",
  "data": {...},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Message Types

#### intent.created
Sent when a new intent is created.

```json
{
  "type": "intent.created",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "type": "action",
    "content": "Adjust HVAC temperature to 72°F",
    "context": {...},
    "priority": "high",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### action_graph.updated
Sent when an action graph is updated.

```json
{
  "type": "action_graph.updated",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### memory.updated
Sent when memory is updated.

```json
{
  "type": "memory.updated",
  "data": {
    "key": "session_123",
    "value": {...},
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### reflection.completed
Sent when reflection is completed.

```json
{
  "type": "reflection.completed",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "type": "outcome",
    "score": 0.9,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "content",
      "reason": "Field is required"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Codes

- `VALIDATION_ERROR` - Request validation failed
- `NOT_FOUND` - Resource not found
- `INTERNAL_ERROR` - Internal server error
- `SERVICE_UNAVAILABLE` - Service temporarily unavailable
- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded
- `AUTHENTICATION_ERROR` - Authentication failed
- `AUTHORIZATION_ERROR` - Authorization failed

## Rate Limiting

API requests are rate limited to 100 requests per minute per IP address.

**Headers:**
- `X-RateLimit-Limit` - Rate limit (100)
- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Reset time (Unix timestamp)

## Authentication

UAP supports JWT-based authentication.

**Header:**
```
Authorization: Bearer <jwt_token>
```

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page` - Page number (default: 1)
- `size` - Page size (default: 20, max: 100)

**Response Headers:**
- `X-Total-Count` - Total number of items
- `X-Page-Count` - Total number of pages
- `X-Current-Page` - Current page number
- `X-Page-Size` - Current page size

## Filtering and Sorting

List endpoints support filtering and sorting:

**Query Parameters:**
- `filter` - Filter criteria (JSON)
- `sort` - Sort criteria (JSON)
- `search` - Search query

**Example:**
```
GET /intents?filter={"type":"action"}&sort={"created_at":"desc"}&search="hvac"
```

## SDKs

### Python SDK

```python
from uap_sdk import UAPClient

client = UAPClient("http://localhost:8000")

# Create intent
intent = await client.create_intent(
    type="action",
    content="Adjust HVAC temperature to 72°F",
    context={"room": "conference_room_a"}
)

# Execute action graph
result = await client.execute_action_graph(graph_id)
```

### JavaScript SDK

```javascript
import { UAPClient } from 'uap-sdk';

const client = new UAPClient('http://localhost:8000');

// Create intent
const intent = await client.createIntent({
  type: 'action',
  content: 'Adjust HVAC temperature to 72°F',
  context: { room: 'conference_room_a' }
});

// Execute action graph
const result = await client.executeActionGraph(graphId);
```

## Examples

### Complete HVAC Workflow

```python
import asyncio
from uap_sdk import UAPClient

async def hvac_workflow():
    client = UAPClient("http://localhost:8000")
    
    # Create intent
    intent = await client.create_intent(
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
    graph = await client.create_action_graph(
        nodes=[
            {
                "type": "sensor_read",
                "data": {"sensor": "temperature", "room": "conference_room_a"}
            },
            {
                "type": "hvac_adjust",
                "data": {"room": "conference_room_a", "target_temp": 72}
            }
        ],
        edges=[{"from": "node-1", "to": "node-2"}]
    )
    
    # Execute graph
    result = await client.execute_action_graph(graph.id)
    
    # Create reflection report
    report = await client.create_reflection_report(
        type="outcome",
        evaluations=[{
            "type": "outcome",
            "score": 0.9,
            "feedback": {"efficiency": "high"}
        }]
    )
    
    return result

# Run workflow
result = asyncio.run(hvac_workflow())
```

## Changelog

### Version 1.0.0
- Initial release
- Core UAP functionality
- REST API endpoints
- WebSocket support
- Basic monitoring

### Version 1.1.0
- Enhanced error handling
- Improved logging
- Additional metrics
- Performance optimizations

### Version 1.2.0
- Protocol bridge improvements
- Enhanced reflection engine
- Additional configuration options
- Security enhancements
