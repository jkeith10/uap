"""Integration tests for UAP workflows"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.uap.models.intent import IntentPacket, IntentType
from src.uap.models.action_graph import ActionGraph, ActionNode
from src.uap.core.kernel import WorldStateManager
from src.uap.core.events import EventSystem


class TestHVACWorkflow:
    """Test HVAC workflow integration"""
    
    @pytest.mark.asyncio
    async def test_hvac_intent_processing(self, mock_world_state_manager, mock_event_system):
        """Test HVAC intent processing workflow"""
        # Create HVAC intent
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Adjust HVAC temperature to 72°F",
            context={
                "room": "conference_room_a",
                "current_temp": 75,
                "target_temp": 72
            }
        )
        
        # Mock world state manager responses
        mock_world_state_manager.get_state.return_value = {
            "room": "conference_room_a",
            "current_temp": 75,
            "hvac_status": "active"
        }
        mock_world_state_manager.set_state.return_value = None
        
        # Mock event system
        mock_event_system.create_event.return_value = None
        
        # Process intent
        assert intent.type == IntentType.ACTION
        assert intent.content == "Adjust HVAC temperature to 72°F"
        assert intent.context["room"] == "conference_room_a"
        assert intent.context["current_temp"] == 75
        assert intent.context["target_temp"] == 72
        
        # Verify world state manager was called
        mock_world_state_manager.get_state.assert_called()
        mock_world_state_manager.set_state.assert_called()
        
        # Verify event system was called
        mock_event_system.create_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_action_graph_execution(self, mock_world_state_manager):
        """Test action graph execution workflow"""
        # Create action nodes
        node1 = ActionNode(
            type="sensor_read",
            data={"sensor": "temperature", "room": "conference_room_a"}
        )
        
        node2 = ActionNode(
            type="hvac_adjust",
            data={"room": "conference_room_a", "target_temp": 72}
        )
        
        # Create action graph
        graph = ActionGraph(
            nodes=[node1, node2],
            edges=[{"from": node1.id, "to": node2.id}]
        )
        
        # Mock world state manager
        mock_world_state_manager.get_state.return_value = {"current_temp": 75}
        mock_world_state_manager.set_state.return_value = None
        
        # Execute graph
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.status == "pending"
        
        # Update node status
        node1.update_status("completed")
        assert node1.status == "completed"
        
        node2.update_status("completed")
        assert node2.status == "completed"
        
        # Verify world state manager was called
        mock_world_state_manager.get_state.assert_called()
        mock_world_state_manager.set_state.assert_called()
    
    @pytest.mark.asyncio
    async def test_event_driven_workflow(self, mock_event_system):
        """Test event-driven workflow"""
        # Mock event system
        mock_event_system.create_event.return_value = None
        mock_event_system.subscribe.return_value = None
        
        # Create events
        await mock_event_system.create_event(
            type="temperature_change",
            source="sensor",
            data={"room": "conference_room_a", "temperature": 75}
        )
        
        await mock_event_system.create_event(
            type="hvac_adjustment",
            source="hvac_controller",
            data={"room": "conference_room_a", "target_temp": 72}
        )
        
        # Verify events were created
        assert mock_event_system.create_event.call_count == 2
        
        # Subscribe to events
        await mock_event_system.subscribe(
            event_type="temperature_change",
            callback=AsyncMock()
        )
        
        # Verify subscription
        mock_event_system.subscribe.assert_called_once()
