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


class UAPAPI:
    """UAP REST API"""
    
    def __init__(
        self,
        world_state_manager,
        event_system,
        mediator,
        memory_bus,
        routing_engine
    ):
        self.world_state_manager = world_state_manager
        self.event_system = event_system
        self.mediator = mediator
        self.memory_bus = memory_bus
        self.routing_engine = routing_engine
    
    async def submit_intent(self, intent: IntentPacket) -> Dict[str, Any]:
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
            result = await self.mediator.process_packet(packet)
            
            # Publish event
            await self.event_system.create_event(
                event_type="intent.created",
                source="api-gateway",
                data={"intent_id": str(intent.id), "result": result.payload}
            )
            
            return {
                "status": "success",
                "intent_id": str(intent.id),
                "result": result.payload
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_action_graph(self, graph: ActionGraph) -> Dict[str, Any]:
        """Create an action graph"""
        try:
            # Validate graph
            errors = graph.validate_graph()
            if errors:
                raise HTTPException(status_code=400, detail=f"Graph validation errors: {errors}")
            
            # Store in PostgreSQL
            graph_id = await self.world_state_manager.postgres_client.create_action_graph(
                graph_id=str(graph.id),
                name=graph.name,
                definition=graph.to_dag_format(),
                status=graph.status.value
            )
            
            return {
                "status": "success",
                "graph_id": graph_id,
                "graph": graph.dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_action_graph(self, graph_id: str) -> Dict[str, Any]:
        """Get an action graph"""
        try:
            graph_data = await self.world_state_manager.postgres_client.get_action_graph(graph_id)
            if not graph_data:
                raise HTTPException(status_code=404, detail="Action graph not found")
            
            return {
                "status": "success",
                "graph": graph_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def query_memories(self, query: MemoryQuery) -> Dict[str, Any]:
        """Query memory streams"""
        try:
            memories = await self.memory_bus.query_memories(query)
            
            return {
                "status": "success",
                "memories": [memory.dict() for memory in memories],
                "count": len(memories)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_reflection_reports(self, query: ReflectionQuery) -> Dict[str, Any]:
        """Get reflection reports"""
        try:
            reports = await self.world_state_manager.postgres_client.get_reflection_reports(
                actor=query.actors[0] if query.actors else None,
                limit=query.limit,
                offset=query.offset
            )
            
            return {
                "status": "success",
                "reports": reports,
                "count": len(reports)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_node_capabilities(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """Get node capabilities"""
        try:
            if node_id:
                capabilities = await self.routing_engine.get_node_capabilities(node_id)
                return {
                    "status": "success",
                    "capabilities": capabilities.__dict__ if capabilities else None
                }
            else:
                nodes = await self.routing_engine.get_available_nodes()
                return {
                    "status": "success",
                    "nodes": nodes
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            memory_stats = await self.memory_bus.get_memory_stats()
            routing_stats = await self.routing_engine.get_routing_stats()
            
            return {
                "status": "success",
                "memory": memory_stats,
                "routing": routing_stats,
                "timestamp": "2024-01-01T10:00:00Z"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


def create_app(
    world_state_manager,
    event_system,
    mediator,
    memory_bus,
    routing_engine
) -> FastAPI:
    """Create FastAPI application"""
    
    app = FastAPI(
        title="Unified Autonomy Protocol (UAP)",
        description="A cross-domain, self-optimizing protocol for intelligent system orchestration",
        version="0.1.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize API
    api = UAPAPI(
        world_state_manager,
        event_system,
        mediator,
        memory_bus,
        routing_engine
    )
    
    # Intent endpoints
    @app.post("/intent")
    async def submit_intent(intent: IntentPacket):
        return await api.submit_intent(intent)
    
    @app.get("/intent/{intent_id}")
    async def get_intent(intent_id: str):
        # Implementation would retrieve intent from storage
        return {"status": "success", "intent_id": intent_id}
    
    # Action graph endpoints
    @app.post("/graph")
    async def create_action_graph(graph: ActionGraph):
        return await api.create_action_graph(graph)
    
    @app.get("/graph/{graph_id}")
    async def get_action_graph(graph_id: str):
        return await api.get_action_graph(graph_id)
    
    @app.get("/graph")
    async def list_action_graphs():
        # Implementation would list all graphs
        return {"status": "success", "graphs": []}
    
    # Memory endpoints
    @app.post("/memory/query")
    async def query_memories(query: MemoryQuery):
        return await api.query_memories(query)
    
    @app.get("/memory/stream/{stream_id}")
    async def get_stream_memories(stream_id: str, limit: int = 100, offset: int = 0):
        memories = await api.memory_bus.get_stream_memories(stream_id, limit, offset)
        return {
            "status": "success",
            "memories": [memory.dict() for memory in memories],
            "count": len(memories)
        }
    
    # Reflection endpoints
    @app.post("/reflect/query")
    async def get_reflection_reports(query: ReflectionQuery):
        return await api.get_reflection_reports(query)
    
    @app.get("/reflect/{report_id}")
    async def get_reflection_report(report_id: str):
        # Implementation would retrieve specific report
        return {"status": "success", "report_id": report_id}
    
    # Node endpoints
    @app.get("/nodes")
    async def get_nodes():
        return await api.get_node_capabilities()
    
    @app.get("/nodes/{node_id}")
    async def get_node(node_id: str):
        return await api.get_node_capabilities(node_id)
    
    @app.post("/nodes/{node_id}/register")
    async def register_node(node_id: str, capabilities: Dict[str, Any]):
        # Implementation would register node
        return {"status": "success", "node_id": node_id}
    
    # System endpoints
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "timestamp": "2024-01-01T10:00:00Z"}
    
    @app.get("/stats")
    async def get_system_stats():
        return await api.get_system_stats()
    
    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                # Echo back the data
                await websocket.send_text(f"Echo: {data}")
        except WebSocketDisconnect:
            pass
    
    return app


if __name__ == "__main__":
    uvicorn.run("rest_api:app", host="0.0.0.0", port=8000, reload=True)
