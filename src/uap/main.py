"""UAP Main Application"""

import asyncio
import logging
from typing import Dict, Any

from .core import WorldStateManager, EventSystem, VersionManager
from .aml import ProtocolMediator, SelfRoutingEngine, DriverRegistry, DelegateRegistry
from .storage import RedisClient, PostgreSQLClient, MemoryBus
from .transport.rest_api import create_app
from .transport.websocket import WebSocketManager


class UAPApplication:
    """Main UAP application"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.redis_client = RedisClient(config["redis"])
        self.postgres_client = PostgreSQLClient(config["postgres"])
        self.memory_bus = MemoryBus(self.redis_client, self.postgres_client)
        
        self.world_state_manager = WorldStateManager(
            self.redis_client,
            self.postgres_client
        )
        
        self.event_system = EventSystem()
        self.version_manager = VersionManager()
        
        self.routing_engine = SelfRoutingEngine(self.postgres_client)
        self.driver_registry = DriverRegistry()
        self.delegate_registry = DelegateRegistry()
        
        self.mediator = ProtocolMediator(
            self.routing_engine,
            self.driver_registry,
            self.delegate_registry
        )
        
        self.websocket_manager = WebSocketManager()
        
        # FastAPI app
        self.app = create_app(
            world_state_manager=self.world_state_manager,
            event_system=self.event_system,
            mediator=self.mediator,
            memory_bus=self.memory_bus,
            routing_engine=self.routing_engine
        )
    
    async def start(self) -> None:
        """Start the UAP application"""
        self.logger.info("Starting UAP application...")
        
        # Connect to storage
        await self.redis_client.connect()
        await self.postgres_client.connect()
        
        # Start core components
        await self.memory_bus.start()
        await self.world_state_manager.start()
        await self.event_system.start()
        await self.mediator.start()
        
        # Connect adapters
        await self.driver_registry.connect_all()
        await self.delegate_registry.connect_all()
        
        # Register default nodes
        await self._register_default_nodes()
        
        self.logger.info("UAP application started successfully")
    
    async def stop(self) -> None:
        """Stop the UAP application"""
        self.logger.info("Stopping UAP application...")
        
        # Stop core components
        await self.mediator.stop()
        await self.event_system.stop()
        await self.world_state_manager.stop()
        await self.memory_bus.stop()
        
        # Disconnect adapters
        await self.delegate_registry.disconnect_all()
        await self.driver_registry.disconnect_all()
        
        # Disconnect from storage
        await self.postgres_client.disconnect()
        await self.redis_client.disconnect()
        
        self.logger.info("UAP application stopped")
    
    async def _register_default_nodes(self) -> None:
        """Register default nodes"""
        # Register HVAC Worker node
        await self.routing_engine.register_node(
            node_id="hvac-worker-1",
            name="HVAC Worker",
            capabilities=[
                "intent_processing",
                "intent_optimize",
                "domain_hvac",
                "action_execution",
                "result_processing"
            ],
            cost_weight=0.8,
            latency_weight=0.9,
            confidence_weight=0.95
        )
        
        # Register CRM Analyzer node
        await self.routing_engine.register_node(
            node_id="crm-analyzer-1",
            name="CRM Analyzer",
            capabilities=[
                "intent_processing",
                "intent_analyze",
                "domain_crm",
                "data_collection",
                "analysis"
            ],
            cost_weight=0.6,
            latency_weight=0.8,
            confidence_weight=0.9
        )
        
        # Register Pricing AI node
        await self.routing_engine.register_node(
            node_id="pricing-ai-1",
            name="Pricing AI",
            capabilities=[
                "intent_processing",
                "intent_optimize",
                "domain_pricing",
                "ai_analysis",
                "prediction"
            ],
            cost_weight=1.0,
            latency_weight=0.7,
            confidence_weight=0.85
        )
        
        self.logger.info("Default nodes registered")


def create_uap_app(config: Dict[str, Any]) -> UAPApplication:
    """Create a UAP application instance"""
    return UAPApplication(config)


# Default configuration
DEFAULT_CONFIG = {
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,
        "max_connections": 10
    },
    "postgres": {
        "host": "localhost",
        "port": 5432,
        "database": "uap",
        "user": "uap",
        "password": "uap_password",
        "min_size": 5,
        "max_size": 20
    }
}


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and run application
    app = create_uap_app(DEFAULT_CONFIG)
    
    async def main():
        await app.start()
        try:
            # Keep running
            await asyncio.sleep(float('inf'))
        except KeyboardInterrupt:
            pass
        finally:
            await app.stop()
    
    asyncio.run(main())
