"""FastAPI REST API for UAP"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from ..models import IntentPacket, ActionGraph, MemoryQuery, ReflectionQuery
from ..models.memory_stream import MemoryStream
from ..models.reflection import ReflectionReport
from ..aml.packets import UAPContextPacket, PacketType, ProtocolType

# Create FastAPI app instance
app = FastAPI(
    title="UAP REST API",
    description="REST API endpoints for UAP",
    version="0.1.0"
)

# Global instances (will be injected)
world_state_manager = None
event_system = None
mediator = None
memory_bus = None
routing_engine = None


async def submit_intent(intent: IntentPacket) -> Dict[str, Any]:
    """Submit an intent for processing"""
    try:
        # Create UAP context packet
        packet = UAPContextPacket(
            type=PacketType.INTENT,
            source_protocol=ProtocolType.REST,
            target_protocol=ProtocolType.REST,
            source_node="api-gateway",
            target_node="intent-processor",
            payload=intent.dict(),
            correlation_id=str(intent.id)
        )
        
        # Process through mediator
        result = await mediator.process_packet(packet)
        
        # Publish event
        await event_system.create_event(
            event_type="intent.created",
            source="api-gateway",
            data={"intent_id": str(intent.id), "result": result.payload}
        )
        
        # Store in world state
        await world_state_manager.set_state(
            f"intent:{intent.id}",
            intent.dict(),
            ttl=3600
        )
        
        return {
            "status": "success",
            "intent_id": str(intent.id),
            "result": result.payload
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_intent(intent_id: str) -> Dict[str, Any]:
    """Get an intent by ID"""
    try:
        state = await world_state_manager.get_state(f"intent:{intent_id}")
        if not state:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        return {
            "status": "success",
            "intent": state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def create_action_graph(graph: ActionGraph) -> Dict[str, Any]:
    """Create an action graph"""
    try:
        # Validate graph
        errors = graph.validate_graph()
        if errors:
            raise HTTPException(status_code=400, detail=f"Graph validation failed: {errors}")
        
        # Store in world state
        await world_state_manager.set_state(
            f"graph:{graph.id}",
            graph.dict(),
            ttl=7200
        )
        
        return {
            "status": "success",
            "graph_id": str(graph.id),
            "graph": graph.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_action_graph(graph_id: str) -> Dict[str, Any]:
    """Get an action graph by ID"""
    try:
        state = await world_state_manager.get_state(f"graph:{graph_id}")
        if not state:
            raise HTTPException(status_code=404, detail="Action graph not found")
        
        return {
            "status": "success",
            "graph": state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def store_memory(memory: MemoryStream) -> Dict[str, Any]:
    """Store a memory stream"""
    try:
        # Store in memory bus
        await memory_bus.store_memory(memory)
        
        return {
            "status": "success",
            "memory_id": str(memory.stream_id),
            "memory": memory.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def query_memory(query: MemoryQuery) -> List[Dict[str, Any]]:
    """Query memory streams"""
    try:
        # Query memory bus
        results = await memory_bus.query_memory(query)
        
        return {
            "status": "success",
            "memories": [memory.dict() for memory in results],
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def generate_reflection(query: ReflectionQuery) -> ReflectionReport:
    """Generate a reflection report"""
    try:
        # Generate reflection
        reflection = await memory_bus.generate_reflection(query)
        
        return {
            "status": "success",
            "reflection": reflection.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_system_status() -> Dict[str, Any]:
    """Get system status"""
    try:
        return {
            "status": "healthy",
            "world_state": await world_state_manager.get_all_states(),
            "memory_stats": await memory_bus.get_stats(),
            "routing_stats": await routing_engine.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add routes to the FastAPI app
@app.post("/api/v1/intents", response_model=Dict[str, Any])
async def create_intent_endpoint(intent: IntentPacket):
    """Create a new intent"""
    return await submit_intent(intent)


@app.get("/api/v1/intents/{intent_id}", response_model=Dict[str, Any])
async def get_intent_endpoint(intent_id: str):
    """Get an intent by ID"""
    return await get_intent(intent_id)


@app.post("/api/v1/graphs", response_model=Dict[str, Any])
async def create_graph_endpoint(graph: ActionGraph):
    """Create a new action graph"""
    return await create_action_graph(graph)


@app.get("/api/v1/graphs/{graph_id}", response_model=Dict[str, Any])
async def get_graph_endpoint(graph_id: str):
    """Get an action graph by ID"""
    return await get_action_graph(graph_id)


@app.post("/api/v1/memory", response_model=Dict[str, Any])
async def store_memory_endpoint(memory: MemoryStream):
    """Store a memory stream"""
    return await store_memory(memory)


@app.post("/api/v1/memory/query", response_model=Dict[str, Any])
async def query_memory_endpoint(query: MemoryQuery):
    """Query memory streams"""
    return await query_memory(query)


@app.post("/api/v1/reflections", response_model=Dict[str, Any])
async def generate_reflection_endpoint(query: ReflectionQuery):
    """Generate a reflection report"""
    return await generate_reflection(query)


@app.get("/api/v1/status", response_model=Dict[str, Any])
async def get_status_endpoint():
    """Get system status"""
    return await get_system_status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)