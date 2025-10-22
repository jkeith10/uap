# UAP Examples

This directory contains complete, working examples demonstrating UAP capabilities.

## Available Examples

### 1. HVAC Workflow (Basic)
**File**: `hvac_workflow/workflow.py`
- Basic HVAC optimization workflow
- Demonstrates intent processing and action graphs
- Shows memory storage and reflection

### 2. Multi-Agent Collaboration
**File**: `multi_agent/collaboration.py`
- Multiple agents working together
- Agent-to-agent communication
- Shared context and memory
- Collective decision making

### 3. Real-Time Monitoring
**File**: `realtime_monitoring/dashboard.py`
- Real-time event streaming
- WebSocket integration
- Live metrics and updates
- Dashboard visualization

### 4. Batch Processing
**File**: `batch_processing/workflow.py`
- Process multiple tasks in parallel
- Batch optimization
- Progress tracking
- Result aggregation

### 5. Protocol Bridging
**File**: `protocol_bridge/integration.py`
- MCP, A2A, and ACP integration
- Protocol translation
- Multi-protocol workflows
- Cross-protocol communication

## Running Examples

```bash
# Run specific example
python examples/hvac_workflow/workflow.py

# Or use the CLI
uap demo  # Runs built-in demo

# Run with Docker
docker-compose -f docker-compose.dev.yml run uap python examples/hvac_workflow/workflow.py
```

## Example Structure

Each example includes:
- Complete working code
- Configuration file
- README with explanation
- Expected output
- Troubleshooting tips
