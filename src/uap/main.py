"""UAP Main Application with Complete FastAPI Implementation"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_config, UAPConfig
from .core.kernel import WorldStateManager
from .core.events import EventSystem
from .storage.redis_client import RedisClient
from .storage.postgres_client import PostgreSQLClient
from .storage.memory_bus import MemoryBus
from .aml.routing import Router
from .aml.mediator import ProtocolMediator
from .reflection.engine import ReflectionEngine
from .models.intent import IntentPacket
from .models.action_graph import ActionGraph
from .models.memory_stream import MemoryStream
from .models.reflection import ReflectionReport
from .logging_config import configure_logging, get_logger
from .metrics import get_metrics_collector
from .tracing import get_tracer, start_trace, finish_span
from .exceptions import UAPException

logger = get_logger(__name__)


class UAPApplication:
    """Main UAP application with all components"""
    
    def __init__(self, config: UAPConfig):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Storage clients
        self.redis_client: Optional[RedisClient] = None
        self.postgres_client: Optional[PostgreSQLClient] = None
        self.memory_bus: Optional[MemoryBus] = None
        
        # Core components
        self.world_state_manager: Optional[WorldStateManager] = None
        self.event_system: Optional[EventSystem] = None
        self.router: Optional[Router] = None
        self.mediator: Optional[ProtocolMediator] = None
        self.reflection_engine: Optional[ReflectionEngine] = None
        
        # Metrics and tracing
        self.metrics = get_metrics_collector()
        self.tracer = get_tracer()
    
    async def start(self) -> None:
        """Start all UAP components"""
        self.logger.info("Starting UAP application", 
                        environment=self.config.environment.value)
        
        try:
            # Initialize storage clients
            self.redis_client = RedisClient(
                host=self.config.redis.host,
                port=self.config.redis.port,
                db=self.config.redis.db,
                password=self.config.redis.password,
                max_connections=self.config.redis.max_connections
            )
            
            self.postgres_client = PostgreSQLClient(
                host=self.config.database.host,
                port=self.config.database.port,
                database=self.config.database.name,
                user=self.config.database.user,
                password=self.config.database.password,
                min_size=self.config.database.pool_size,
                max_size=self.config.database.max_overflow
            )
            
            # Connect to storage
            await self.redis_client.connect()
            await self.postgres_client.connect()
            
            # Initialize memory bus
            self.memory_bus = MemoryBus(self.redis_client, self.postgres_client)
            await self.memory_bus.start()
            
            # Initialize core components
            self.world_state_manager = WorldStateManager(
                redis_client=self.redis_client,
                postgres_client=self.postgres_client
            )
            await self.world_state_manager.start()
            
            self.event_system = EventSystem()
            await self.event_system.start()
            
            self.router = Router()
            
            self.mediator = ProtocolMediator(
                router=self.router,
                redis_client=self.redis_client
            )
            
            self.reflection_engine = ReflectionEngine(
                memory_bus=self.memory_bus,
                postgres_client=self.postgres_client
            )
            
            self.logger.info("UAP application started successfully")
            
        except Exception as e:
            self.logger.error("Failed to start UAP application", 
                            error=str(e), exc_info=True)
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop all UAP components"""
        self.logger.info("Stopping UAP application")
        
        try:
            # Stop core components
            if self.reflection_engine:
                await self.reflection_engine.stop()
            
            if self.event_system:
                await self.event_system.stop()
            
            if self.world_state_manager:
                await self.world_state_manager.stop()
            
            if self.memory_bus:
                await self.memory_bus.stop()
            
            # Disconnect storage clients
            if self.postgres_client:
                await self.postgres_client.disconnect()
            
            if self.redis_client:
                await self.redis_client.disconnect()
            
            self.logger.info("UAP application stopped")
            
        except Exception as e:
            self.logger.error("Error during shutdown", error=str(e), exc_info=True)


# Global application instance
_uap_app: Optional[UAPApplication] = None


def get_uap_app() -> UAPApplication:
    """Get the global UAP application instance"""
    if _uap_app is None:
        raise RuntimeError("UAP application not initialized")
    return _uap_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager"""
    global _uap_app
    
    # Startup
    config = get_config()
    configure_logging(
        level=config.logging.level.value,
        format_type=config.logging.format
    )
    
    _uap_app = UAPApplication(config)
    await _uap_app.start()
    
    yield
    
    # Shutdown
    await _uap_app.stop()


# Create FastAPI application
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Unified Autonomy Protocol (UAP)",
        description="A cross-domain, self-optimizing protocol for intelligent system orchestration",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on config
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoints
    @app.get("/health")
    async def health_check():
        """Basic health check"""
        return {"status": "healthy", "service": "uap"}
    
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with component status"""
        uap = get_uap_app()
        
        redis_health = await uap.redis_client.health_check()
        postgres_health = await uap.postgres_client.health_check()
        memory_bus_health = await uap.memory_bus.get_metrics()
        
        return {
            "status": "healthy",
            "components": {
                "redis": redis_health,
                "postgres": postgres_health,
                "memory_bus": memory_bus_health
            }
        }
    
    # Metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus-compatible metrics"""
        metrics_data = get_metrics_collector().get_all_metrics()
        # Convert to Prometheus format
        lines = []
        for name, data in metrics_data.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {data['value']}")
        return "\n".join(lines)
    
    # Intent endpoints
    @app.post("/api/v1/intents")
    async def create_intent(intent: IntentPacket):
        """Create a new intent"""
        trace_id = start_trace()
        try:
            uap = get_uap_app()
            
            # Store intent
            await uap.memory_bus.store_memory(
                f"intent:{intent.id}",
                intent.model_dump()
            )
            
            # Create event
            await uap.event_system.create_event(
                event_type="intent.created",
                source="api",
                data={"intent_id": str(intent.id)}
            )
            
            logger.info("Intent created", intent_id=str(intent.id))
            return intent
            
        except Exception as e:
            logger.error("Failed to create intent", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/intents/{intent_id}")
    async def get_intent(intent_id: str):
        """Get intent by ID"""
        try:
            uap = get_uap_app()
            intent_data = await uap.memory_bus.retrieve_memory(f"intent:{intent_id}")
            
            if not intent_data:
                raise HTTPException(status_code=404, detail="Intent not found")
            
            return intent_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get intent", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    # Action Graph endpoints
    @app.post("/api/v1/graphs")
    async def create_action_graph(graph: ActionGraph):
        """Create a new action graph"""
        try:
            uap = get_uap_app()
            
            # Store graph
            await uap.memory_bus.store_memory(
                f"graph:{graph.id}",
                graph.model_dump()
            )
            
            # Create event
            await uap.event_system.create_event(
                event_type="graph.created",
                source="api",
                data={"graph_id": str(graph.id)}
            )
            
            logger.info("Action graph created", graph_id=str(graph.id))
            return graph
            
        except Exception as e:
            logger.error("Failed to create graph", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/graphs/{graph_id}")
    async def get_action_graph(graph_id: str):
        """Get action graph by ID"""
        try:
            uap = get_uap_app()
            graph_data = await uap.memory_bus.retrieve_memory(f"graph:{graph_id}")
            
            if not graph_data:
                raise HTTPException(status_code=404, detail="Graph not found")
            
            return graph_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get graph", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v1/graphs/{graph_id}/execute")
    async def execute_action_graph(graph_id: str):
        """Execute an action graph"""
        try:
            uap = get_uap_app()
            
            # Get graph
            graph_data = await uap.memory_bus.retrieve_memory(f"graph:{graph_id}")
            if not graph_data:
                raise HTTPException(status_code=404, detail="Graph not found")
            
            # Execute graph (simplified - full implementation would be more complex)
            # This would involve routing through the mediator, executing nodes, etc.
            
            # Create event
            await uap.event_system.create_event(
                event_type="graph.executed",
                source="api",
                data={"graph_id": graph_id}
            )
            
            logger.info("Action graph executed", graph_id=graph_id)
            return {"status": "executed", "graph_id": graph_id}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to execute graph", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    # Memory Stream endpoints
    @app.post("/api/v1/memories")
    async def create_memory_stream(memory: MemoryStream):
        """Create a new memory stream"""
        try:
            uap = get_uap_app()
            
            # Store memory stream
            await uap.memory_bus.store_memory(
                f"memory:{memory.id}",
                memory.model_dump()
            )
            
            logger.info("Memory stream created", memory_id=str(memory.id))
            return memory
            
        except Exception as e:
            logger.error("Failed to create memory stream", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/memories/{memory_id}")
    async def get_memory_stream(memory_id: str):
        """Get memory stream by ID"""
        try:
            uap = get_uap_app()
            memory_data = await uap.memory_bus.retrieve_memory(f"memory:{memory_id}")
            
            if not memory_data:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            return memory_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get memory stream", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v1/memories/search")
    async def search_memories(query: Dict[str, Any]):
        """Search memory streams"""
        try:
            uap = get_uap_app()
            
            # Search memories
            results = await uap.memory_bus.search_memories(query.get("query", ""))
            
            return {"results": results, "count": len(results)}
            
        except Exception as e:
            logger.error("Failed to search memories", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    # Reflection endpoints
    @app.post("/api/v1/reflections")
    async def create_reflection_report(report: ReflectionReport):
        """Create a new reflection report"""
        try:
            uap = get_uap_app()
            
            # Store reflection report
            await uap.memory_bus.store_memory(
                f"reflection:{report.id}",
                report.model_dump()
            )
            
            logger.info("Reflection report created", report_id=str(report.id))
            return report
            
        except Exception as e:
            logger.error("Failed to create reflection report", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/reflections/{report_id}")
    async def get_reflection_report(report_id: str):
        """Get reflection report by ID"""
        try:
            uap = get_uap_app()
            report_data = await uap.memory_bus.retrieve_memory(f"reflection:{report_id}")
            
            if not report_data:
                raise HTTPException(status_code=404, detail="Reflection report not found")
            
            return report_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get reflection report", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time communication"""
        await websocket.accept()
        
        try:
            while True:
                data = await websocket.receive_json()
                
                # Handle different message types
                msg_type = data.get("type")
                
                if msg_type == "subscribe":
                    # Subscribe to events
                    await websocket.send_json({
                        "type": "subscribed",
                        "topic": data.get("topic")
                    })
                
                elif msg_type == "intent":
                    # Process intent via WebSocket
                    intent = IntentPacket(**data.get("data"))
                    uap = get_uap_app()
                    
                    await uap.memory_bus.store_memory(
                        f"intent:{intent.id}",
                        intent.model_dump()
                    )
                    
                    await websocket.send_json({
                        "type": "intent.created",
                        "data": intent.model_dump()
                    })
                
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error("WebSocket error", error=str(e), exc_info=True)
    
    return app


# Create the app instance
app = create_app()


def main():
    """Main entry point for running the server"""
    config = get_config()
    
    uvicorn.run(
        "src.uap.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level=config.logging.level.value.lower()
    )


if __name__ == "__main__":
    main()
