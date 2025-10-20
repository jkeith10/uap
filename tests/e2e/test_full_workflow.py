"""End-to-end tests for complete UAP workflows"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.uap.models.intent import IntentPacket, IntentType
from src.uap.models.action_graph import ActionGraph, ActionNode
from src.uap.models.memory_stream import MemoryStream, MemoryEntry
from src.uap.models.reflection import ReflectionReport, EvaluationResult
from src.uap.core.kernel import WorldStateManager
from src.uap.core.events import EventSystem
from src.uap.storage.memory_bus import MemoryBus


class TestCompleteUAPWorkflow:
    """Test complete UAP workflow from intent to reflection"""
    
    @pytest.mark.asyncio
    async def test_complete_hvac_workflow(
        self,
        mock_world_state_manager,
        mock_event_system,
        mock_memory_bus
    ):
        """Test complete HVAC workflow from intent to reflection"""
        
        # Step 1: Create intent
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Optimize HVAC for conference room A",
            context={
                "room": "conference_room_a",
                "occupancy": 8,
                "current_temp": 75,
                "target_temp": 72
            }
        )
        
        # Step 2: Create action graph
        sensor_node = ActionNode(
            type="sensor_read",
            data={"sensor": "temperature", "room": "conference_room_a"}
        )
        
        occupancy_node = ActionNode(
            type="occupancy_check",
            data={"room": "conference_room_a"}
        )
        
        hvac_node = ActionNode(
            type="hvac_adjust",
            data={"room": "conference_room_a", "target_temp": 72}
        )
        
        graph = ActionGraph(
            nodes=[sensor_node, occupancy_node, hvac_node],
            edges=[
                {"from": sensor_node.id, "to": hvac_node.id},
                {"from": occupancy_node.id, "to": hvac_node.id}
            ]
        )
        
        # Step 3: Mock world state manager
        mock_world_state_manager.get_state.return_value = {
            "room": "conference_room_a",
            "current_temp": 75,
            "occupancy": 8,
            "hvac_status": "active"
        }
        mock_world_state_manager.set_state.return_value = None
        
        # Step 4: Mock event system
        mock_event_system.create_event.return_value = None
        
        # Step 5: Mock memory bus
        mock_memory_bus.store_memory.return_value = "memory_id"
        mock_memory_bus.retrieve_memory.return_value = {
            "previous_temp": 74,
            "previous_occupancy": 6
        }
        
        # Step 6: Execute workflow
        # Process intent
        assert intent.type == IntentType.ACTION
        assert intent.context["room"] == "conference_room_a"
        
        # Execute action graph
        sensor_node.update_status("completed")
        occupancy_node.update_status("completed")
        hvac_node.update_status("completed")
        
        # Create memory stream
        memory_entry = MemoryEntry(
            type="workflow_completion",
            data={
                "intent_id": intent.id,
                "graph_id": graph.id,
                "result": "success"
            }
        )
        
        memory_stream = MemoryStream(
            granularity="session",
            entries=[memory_entry]
        )
        
        # Create reflection report
        evaluation = EvaluationResult(
            type="outcome",
            score=0.9,
            feedback={
                "efficiency": "high",
                "accuracy": "excellent",
                "user_satisfaction": "high"
            }
        )
        
        reflection_report = ReflectionReport(
            type="outcome",
            evaluations=[evaluation]
        )
        
        # Step 7: Verify workflow completion
        assert len(graph.nodes) == 3
        assert all(node.status == "completed" for node in graph.nodes)
        assert len(memory_stream.entries) == 1
        assert reflection_report.evaluations[0].score == 0.9
        
        # Verify all components were called
        mock_world_state_manager.get_state.assert_called()
        mock_world_state_manager.set_state.assert_called()
        mock_event_system.create_event.assert_called()
        mock_memory_bus.store_memory.assert_called()
        mock_memory_bus.retrieve_memory.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(
        self,
        mock_world_state_manager,
        mock_event_system,
        mock_memory_bus
    ):
        """Test error handling in complete workflow"""
        
        # Create intent with invalid data
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Invalid HVAC command",
            context={"room": "nonexistent_room"}
        )
        
        # Mock world state manager to return None (room not found)
        mock_world_state_manager.get_state.return_value = None
        
        # Mock event system for error event
        mock_event_system.create_event.return_value = None
        
        # Mock memory bus for error storage
        mock_memory_bus.store_memory.return_value = "error_memory_id"
        
        # Execute workflow with error
        assert intent.context["room"] == "nonexistent_room"
        
        # Verify error handling
        mock_world_state_manager.get_state.assert_called()
        mock_event_system.create_event.assert_called()
        mock_memory_bus.store_memory.assert_called()
    
    @pytest.mark.asyncio
    async def test_multi_room_workflow(
        self,
        mock_world_state_manager,
        mock_event_system,
        mock_memory_bus
    ):
        """Test multi-room HVAC workflow"""
        
        rooms = ["conference_room_a", "conference_room_b", "office_1"]
        intents = []
        graphs = []
        
        for room in rooms:
            # Create intent for each room
            intent = IntentPacket(
                type=IntentType.ACTION,
                content=f"Optimize HVAC for {room}",
                context={
                    "room": room,
                    "current_temp": 75,
                    "target_temp": 72
                }
            )
            intents.append(intent)
            
            # Create action graph for each room
            node = ActionNode(
                type="hvac_adjust",
                data={"room": room, "target_temp": 72}
            )
            
            graph = ActionGraph(nodes=[node], edges=[])
            graphs.append(graph)
        
        # Mock world state manager for multiple rooms
        mock_world_state_manager.get_state.return_value = {
            "current_temp": 75,
            "hvac_status": "active"
        }
        mock_world_state_manager.set_state.return_value = None
        
        # Mock event system
        mock_event_system.create_event.return_value = None
        
        # Mock memory bus
        mock_memory_bus.store_memory.return_value = "memory_id"
        
        # Execute multi-room workflow
        assert len(intents) == 3
        assert len(graphs) == 3
        
        for i, (intent, graph) in enumerate(zip(intents, graphs)):
            assert intent.context["room"] == rooms[i]
            assert len(graph.nodes) == 1
            assert graph.nodes[0].data["room"] == rooms[i]
        
        # Verify all components were called for each room
        assert mock_world_state_manager.get_state.call_count == 3
        assert mock_world_state_manager.set_state.call_count == 3
        assert mock_event_system.create_event.call_count == 3
        assert mock_memory_bus.store_memory.call_count == 3
