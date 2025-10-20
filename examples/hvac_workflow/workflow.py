"""HVAC Workflow Example for UAP"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

from src.uap.models import IntentPacket, ActionGraph, ActionNode, ActionEdge, GraphStatus
from src.uap.models.memory_stream import MemoryStream, MemoryGranularity, RetentionPolicy
from src.uap.models.reflection import ReflectionReport, EvaluationResult
from src.uap.aml.packets import UAPContextPacket, PacketType, ProtocolType


class HVACWorkflow:
    """Complete HVAC quote optimization workflow"""
    
    def __init__(self, uap_app):
        self.uap_app = uap_app
        self.workflow_id = "hvac-optimization-v1"
    
    async def run_workflow(self, goal: str) -> Dict[str, Any]:
        """Run the complete HVAC optimization workflow"""
        print(f"Starting HVAC workflow: {goal}")
        
        # Step 1: Create intent packet
        intent = IntentPacket(
            type="optimize",
            goal=goal,
            context_ref="BellOps/v1.2",
            priority=0.8,
            metadata={
                "domain": "hvac",
                "organization": "BellOps",
                "version": "1.2"
            }
        )
        
        # Step 2: Create action graph
        action_graph = await self._create_action_graph()
        
        # Step 3: Execute workflow
        results = await self._execute_workflow(intent, action_graph)
        
        # Step 4: Create reflection report
        reflection = await self._create_reflection_report(intent, results)
        
        # Step 5: Store in memory
        await self._store_workflow_memory(intent, results, reflection)
        
        return {
            "intent": intent,
            "action_graph": action_graph,
            "results": results,
            "reflection": reflection,
            "workflow_id": self.workflow_id
        }
    
    async def _create_action_graph(self) -> ActionGraph:
        """Create the HVAC optimization action graph"""
        graph = ActionGraph(
            name="HVAC Quote Optimization",
            description="Optimize HVAC quoting workflow for BellOps",
            status=GraphStatus.DRAFT
        )
        
        # Add nodes
        lead_capture_node = ActionNode(
            id="lead-capture",
            name="Lead Capture",
            type="data_collection",
            config={
                "source": "crm_api",
                "fields": ["contact", "lead_score", "source", "property_type"],
                "filters": {"domain": "hvac"}
            },
            timeout=300,
            retry_count=3
        )
        
        estimate_accuracy_node = ActionNode(
            id="estimate-accuracy",
            name="Estimate Accuracy",
            type="analysis",
            config={
                "model": "pricing_ai",
                "algorithm": "regression",
                "features": ["property_size", "age", "location", "equipment_type"]
            },
            timeout=600,
            retry_count=2
        )
        
        follow_up_cadence_node = ActionNode(
            id="follow-up-cadence",
            name="Follow-up Cadence",
            type="action",
            config={
                "strategy": "automated",
                "channels": ["email", "sms", "call"],
                "schedule": "adaptive"
            },
            timeout=180,
            retry_count=1
        )
        
        # Add dependencies
        estimate_accuracy_node.add_dependency("lead-capture")
        follow_up_cadence_node.add_dependency("estimate-accuracy")
        
        # Add nodes to graph
        graph.add_node(lead_capture_node)
        graph.add_node(estimate_accuracy_node)
        graph.add_node(follow_up_cadence_node)
        
        # Add edges
        graph.add_edge(ActionEdge(
            from_node="lead-capture",
            to_node="estimate-accuracy",
            condition="success",
            data_mapping={"lead_data": "input_data"}
        ))
        
        graph.add_edge(ActionEdge(
            from_node="estimate-accuracy",
            to_node="follow-up-cadence",
            condition="success",
            data_mapping={"estimate": "input_data"}
        ))
        
        # Validate graph
        errors = graph.validate_graph()
        if errors:
            raise ValueError(f"Graph validation errors: {errors}")
        
        return graph
    
    async def _execute_workflow(
        self,
        intent: IntentPacket,
        action_graph: ActionGraph
    ) -> Dict[str, Any]:
        """Execute the action graph workflow"""
        results = {}
        
        # Simulate workflow execution
        for node in action_graph.nodes:
            print(f"Executing node: {node.name}")
            
            # Create UAP context packet
            packet = UAPContextPacket(
                type=PacketType.ACTION,
                source_protocol=ProtocolType.REST,
                target_protocol=ProtocolType.REST,
                source_node="workflow-engine",
                target_node=f"{node.type}-worker",
                payload={
                    "node_id": node.id,
                    "node_type": node.type,
                    "config": node.config,
                    "intent": intent.dict()
                },
                metadata={
                    "timeout": node.timeout,
                    "retry_count": node.retry_count
                }
            )
            
            # Process packet through mediator
            result = await self.uap_app.mediator.process_packet(packet)
            
            # Store result
            results[node.id] = {
                "status": "success",
                "result": result.payload,
                "execution_time": 150,  # Simulated
                "confidence": 0.85
            }
            
            # Simulate processing time
            await asyncio.sleep(0.1)
        
        return results
    
    async def _create_reflection_report(
        self,
        intent: IntentPacket,
        results: Dict[str, Any]
    ) -> ReflectionReport:
        """Create reflection report for the workflow"""
        
        # Calculate overall performance
        total_execution_time = sum(r.get("execution_time", 0) for r in results.values())
        avg_confidence = sum(r.get("confidence", 0) for r in results.values()) / len(results)
        
        # Create evaluation
        evaluation = EvaluationResult(
            score=avg_confidence,
            metrics={
                "execution_time": total_execution_time,
                "success_rate": 1.0,
                "accuracy": avg_confidence,
                "efficiency": 0.8
            },
            feedback="Workflow executed successfully with good performance",
            recommendations=[
                "Consider caching frequently accessed data",
                "Optimize data collection process",
                "Implement parallel processing for independent nodes"
            ]
        )
        
        # Create reflection report
        reflection = ReflectionReport(
            report_id=f"reflection-{self.workflow_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            actor="Agent:HVAC.Workflow",
            intent=intent.dict(),
            context={
                "workflow_id": self.workflow_id,
                "domain": "hvac",
                "organization": "BellOps"
            },
            result=results,
            confidence=avg_confidence,
            next_action="Optimize routing based on performance data",
            evaluation=evaluation,
            recommendations={
                "routing_changes": [
                    {
                        "node_id": "pricing-ai-1",
                        "weight_adjustment": 0.1,
                        "reason": "Improved accuracy observed"
                    }
                ],
                "parameter_tuning": {
                    "confidence_threshold": 0.85,
                    "timeout_multiplier": 1.2
                }
            }
        )
        
        return reflection
    
    async def _store_workflow_memory(
        self,
        intent: IntentPacket,
        results: Dict[str, Any],
        reflection: ReflectionReport
    ) -> None:
        """Store workflow results in memory bus"""
        
        # Create memory stream entry
        memory = MemoryStream(
            stream_id=f"BellOps/hvac/workflow/{self.workflow_id}",
            actor="Agent:HVAC.Workflow",
            intent=intent.dict(),
            context={
                "workflow_id": self.workflow_id,
                "domain": "hvac",
                "organization": "BellOps"
            },
            result=results,
            confidence=reflection.confidence,
            next_action=reflection.next_action,
            granularity=MemoryGranularity.TASK,
            retention_policy=RetentionPolicy.PERMANENT
        )
        
        # Store in memory bus
        await self.uap_app.memory_bus.store_memory(memory)
        
        print(f"Workflow memory stored: {memory.stream_id}")


async def run_hvac_example():
    """Run the HVAC workflow example"""
    from src.uap.main import create_uap_app, DEFAULT_CONFIG
    
    # Create UAP application
    app = create_uap_app(DEFAULT_CONFIG)
    
    try:
        # Start application
        await app.start()
        
        # Create and run HVAC workflow
        hvac_workflow = HVACWorkflow(app)
        
        # Run the workflow
        result = await hvac_workflow.run_workflow(
            "Increase conversion rate on service quotes by optimizing pricing accuracy and follow-up timing"
        )
        
        print("\n=== HVAC Workflow Results ===")
        print(f"Workflow ID: {result['workflow_id']}")
        print(f"Intent: {result['intent'].goal}")
        print(f"Action Graph: {result['action_graph'].name}")
        print(f"Results: {len(result['results'])} nodes executed")
        print(f"Reflection Score: {result['reflection'].evaluation.score}")
        
        # Query memory to verify storage
        from src.uap.models.memory_stream import MemoryQuery
        
        query = MemoryQuery(
            stream_ids=["BellOps/hvac/workflow/*"],
            granularity=[MemoryGranularity.TASK],
            limit=10
        )
        
        memories = await app.memory_bus.query_memories(query)
        print(f"\nStored memories: {len(memories)}")
        
        for memory in memories:
            print(f"- {memory.stream_id}: {memory.actor}")
        
    finally:
        # Stop application
        await app.stop()


if __name__ == "__main__":
    asyncio.run(run_hvac_example())
