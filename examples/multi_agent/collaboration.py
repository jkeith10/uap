"""Multi-Agent Collaboration Example for UAP"""

from __future__ import annotations

import asyncio
from typing import List, Dict, Any

from src.uap.client import AsyncUAPClient
from src.uap.models.intent import IntentPacket, IntentType, IntentPriority
from src.uap.models.action_graph import ActionGraph, ActionNode, GraphStatus
from src.uap.models.memory_stream import MemoryStream, MemoryEntry, MemoryGranularity
from src.uap.models.reflection import ReflectionReport, EvaluationResult, EvaluationType


class Agent:
    """Base agent class"""
    
    def __init__(self, agent_id: str, name: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.memory: List[Dict[str, Any]] = []
    
    async def process_intent(self, intent: IntentPacket) -> Dict[str, Any]:
        """Process an intent based on agent capabilities"""
        print(f"[{self.name}] Processing intent: {intent.content}")
        
        result = {
            "agent_id": self.agent_id,
            "intent_id": str(intent.id),
            "status": "completed",
            "result": f"Processed by {self.name}",
            "capabilities_used": self.capabilities
        }
        
        # Store in memory
        self.memory.append(result)
        
        return result
    
    async def share_memory(self, other_agent: Agent) -> None:
        """Share memory with another agent"""
        print(f"[{self.name}] Sharing memory with {other_agent.name}")
        other_agent.memory.extend(self.memory)


async def multi_agent_workflow():
    """Demonstrate multi-agent collaboration"""
    
    print("=" * 60)
    print("UAP Multi-Agent Collaboration Example")
    print("=" * 60)
    print()
    
    # Create agents with different capabilities
    sensor_agent = Agent(
        agent_id="sensor-001",
        name="Sensor Agent",
        capabilities=["data_collection", "sensor_reading", "monitoring"]
    )
    
    analyzer_agent = Agent(
        agent_id="analyzer-001",
        name="Analyzer Agent",
        capabilities=["data_analysis", "pattern_recognition", "prediction"]
    )
    
    optimizer_agent = Agent(
        agent_id="optimizer-001",
        name="Optimizer Agent",
        capabilities=["optimization", "decision_making", "execution"]
    )
    
    # Connect to UAP
    async with AsyncUAPClient("http://localhost:8000") as client:
        
        # Step 1: Sensor Agent collects data
        print("\n1. Sensor Agent: Collecting data...")
        sensor_intent = IntentPacket(
            type=IntentType.QUERY,
            content="Collect temperature and occupancy data from all rooms",
            context={
                "rooms": ["conference_a", "conference_b", "office_1"],
                "sensors": ["temperature", "occupancy", "humidity"]
            },
            priority=IntentPriority.HIGH
        )
        
        sensor_result = await sensor_agent.process_intent(sensor_intent)
        await client.create_intent(sensor_intent)
        
        # Step 2: Share data with Analyzer Agent
        print("\n2. Sharing data with Analyzer Agent...")
        await sensor_agent.share_memory(analyzer_agent)
        
        # Step 3: Analyzer Agent analyzes data
        print("\n3. Analyzer Agent: Analyzing patterns...")
        analyzer_intent = IntentPacket(
            type=IntentType.ANALYZE,
            content="Analyze HVAC patterns and identify optimization opportunities",
            context={
                "data_source": sensor_result,
                "analysis_type": "optimization"
            },
            priority=IntentPriority.HIGH
        )
        
        analyzer_result = await analyzer_agent.process_intent(analyzer_intent)
        await client.create_intent(analyzer_intent)
        
        # Step 4: Share analysis with Optimizer Agent
        print("\n4. Sharing analysis with Optimizer Agent...")
        await analyzer_agent.share_memory(optimizer_agent)
        
        # Step 5: Optimizer Agent makes decisions
        print("\n5. Optimizer Agent: Making optimization decisions...")
        optimizer_intent = IntentPacket(
            type=IntentType.OPTIMIZE,
            content="Optimize HVAC settings across all rooms",
            context={
                "analysis_result": analyzer_result,
                "target": "energy_efficiency",
                "constraints": {"comfort_level": "high"}
            },
            priority=IntentPriority.CRITICAL
        )
        
        optimizer_result = await optimizer_agent.process_intent(optimizer_intent)
        await client.create_intent(optimizer_intent)
        
        # Step 6: Create action graph for execution
        print("\n6. Creating coordinated action graph...")
        
        # Sensor node
        sensor_node = ActionNode(
            type="sensor_read",
            data={
                "agent": sensor_agent.agent_id,
                "sensors": ["temperature", "occupancy"]
            }
        )
        
        # Analysis node
        analysis_node = ActionNode(
            type="analyze",
            data={
                "agent": analyzer_agent.agent_id,
                "algorithm": "pattern_recognition"
            }
        )
        
        # Optimization node
        optimization_node = ActionNode(
            type="optimize",
            data={
                "agent": optimizer_agent.agent_id,
                "target": "energy_efficiency"
            }
        )
        
        # Execution node
        execution_node = ActionNode(
            type="execute",
            data={
                "agent": optimizer_agent.agent_id,
                "action": "adjust_hvac"
            }
        )
        
        # Create graph
        graph = ActionGraph(
            nodes=[sensor_node, analysis_node, optimization_node, execution_node],
            edges=[
                {"from": str(sensor_node.id), "to": str(analysis_node.id)},
                {"from": str(analysis_node.id), "to": str(optimization_node.id)},
                {"from": str(optimization_node.id), "to": str(execution_node.id)}
            ],
            status=GraphStatus.PENDING
        )
        
        created_graph = await client.create_action_graph(graph)
        print(f"   Graph created: {created_graph.id}")
        
        # Step 7: Execute the coordinated workflow
        print("\n7. Executing coordinated workflow...")
        execution_result = await client.execute_action_graph(created_graph.id)
        print(f"   Execution status: {execution_result.get('status')}")
        
        # Step 8: Create shared memory
        print("\n8. Creating shared memory stream...")
        
        # Combine all agent memories
        all_memories = (
            sensor_agent.memory +
            analyzer_agent.memory +
            optimizer_agent.memory
        )
        
        memory_entries = [
            MemoryEntry(
                type="agent_action",
                data=mem
            )
            for mem in all_memories
        ]
        
        shared_memory = MemoryStream(
            granularity=MemoryGranularity.SESSION,
            entries=memory_entries
        )
        
        created_memory = await client.create_memory_stream(shared_memory)
        print(f"   Shared memory created: {created_memory.id}")
        
        # Step 9: Create reflection report
        print("\n9. Creating collaborative reflection report...")
        
        evaluations = [
            EvaluationResult(
                type=EvaluationType.OUTCOME,
                score=0.95,
                feedback={
                    "efficiency": "excellent",
                    "collaboration": "seamless",
                    "agent_coordination": "optimal"
                }
            ),
            EvaluationResult(
                type=EvaluationType.PERFORMANCE,
                score=0.92,
                feedback={
                    "sensor_agent": "fast_response",
                    "analyzer_agent": "accurate_analysis",
                    "optimizer_agent": "effective_optimization"
                }
            )
        ]
        
        reflection = ReflectionReport(
            type="multi_agent_collaboration",
            evaluations=evaluations
        )
        
        created_reflection = await client.create_reflection_report(reflection)
        print(f"   Reflection report created: {created_reflection.id}")
        
        # Step 10: Summary
        print("\n" + "=" * 60)
        print("Multi-Agent Collaboration Summary")
        print("=" * 60)
        print(f"✅ Agents involved: 3")
        print(f"✅ Intents processed: 3")
        print(f"✅ Action graph nodes: 4")
        print(f"✅ Memory entries: {len(memory_entries)}")
        print(f"✅ Average evaluation score: {sum(e.score for e in evaluations) / len(evaluations):.2f}")
        print()
        print("🎉 Multi-agent workflow completed successfully!")
        print()


if __name__ == "__main__":
    asyncio.run(multi_agent_workflow())

