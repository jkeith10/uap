"""UAP main application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from .transport.rest_api import app as rest_app
from .transport.websocket import WebSocketManager
from .storage.redis_client import RedisClient, RedisConfig
from .storage.postgres_client import PostgreSQLClient, PostgreSQLConfig
from .core.events import EventSystem
from .core.kernel import WorldStateManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global instances
redis_client = None
postgres_client = None
event_system = None
world_state_manager = None
websocket_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, postgres_client, event_system, world_state_manager, websocket_manager
    
    logger.info("Starting UAP application")
    
    try:
        # Initialize Redis client
        redis_config = RedisConfig()
        redis_client = RedisClient(redis_config)
        await redis_client.connect()
        logger.info("Redis client connected")
        
        # Initialize PostgreSQL client
        postgres_config = PostgreSQLConfig()
        postgres_client = PostgreSQLClient(postgres_config)
        await postgres_client.connect()
        logger.info("PostgreSQL client connected")
        
        # Initialize event system
        event_system = EventSystem()
        await event_system.start()
        logger.info("Event system started")
        
        # Initialize world state manager
        world_state_manager = WorldStateManager(redis_client, postgres_client)
        logger.info("World state manager initialized")
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketManager()
        logger.info("WebSocket manager initialized")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start UAP application", error=str(e))
        raise
    finally:
        # Cleanup
        logger.info("Shutting down UAP application")
        
        if websocket_manager:
            await websocket_manager.disconnect()
            logger.info("WebSocket manager disconnected")
        
        if event_system:
            await event_system.stop()
            logger.info("Event system stopped")
        
        if world_state_manager:
            await world_state_manager.cleanup()
            logger.info("World state manager cleaned up")
        
        if postgres_client:
            await postgres_client.disconnect()
            logger.info("PostgreSQL client disconnected")
        
        if redis_client:
            await redis_client.disconnect()
            logger.info("Redis client disconnected")


# Create FastAPI app
app = FastAPI(
    title="Unified Autonomy Protocol (UAP)",
    description="Cross-domain, self-optimizing protocol for intelligent system orchestration",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routes
app.include_router(rest_app.router)

# Add WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time communication"""
    if websocket_manager:
        await websocket_manager.handle_connection(websocket)
    else:
        await websocket.close(code=1011, reason="WebSocket manager not available")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "redis": redis_client.is_connected() if redis_client else False,
            "postgres": postgres_client.is_connected() if postgres_client else False,
            "events": event_system.is_running() if event_system else False,
            "websocket": websocket_manager is not None
        }
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # TODO: Implement actual metrics collection
    return {
        "intents_created": 0,
        "graphs_executed": 0,
        "memory_operations": 0,
        "active_connections": websocket_manager.connection_count() if websocket_manager else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)