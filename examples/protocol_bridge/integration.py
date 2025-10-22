"""Protocol Bridge Integration Example for UAP"""

from __future__ import annotations

import asyncio
from typing import Dict, Any

from src.uap.client import AsyncUAPClient
from src.uap.bridges.mcp_bridge import MCPBridge
from src.uap.bridges.a2a_bridge import A2ABridge
from src.uap.bridges.acp_bridge import ACPBridge
from src.uap.models.intent import IntentPacket, IntentType, IntentPriority
from src.uap.aml.packets import UAPContextPacket, PacketType, ProtocolType


async def protocol_bridge_demo():
    """Demonstrate protocol bridging capabilities"""
    
    print("=" * 60)
    print("UAP Protocol Bridge Integration Example")
    print("=" * 60)
    print()
    
    # Connect to UAP
    async with AsyncUAPClient("http://localhost:8000") as client:
        
        # Step 1: MCP Bridge Example
        print("1. MCP (Model Context Protocol) Bridge")
        print("-" * 40)
        
        mcp_bridge = MCPBridge({
            "server_url": "http://localhost:3000",
            "client_id": "uap-mcp-client"
        })
        
        print("   Initializing MCP bridge...")
        # await mcp_bridge.connect()  # Would connect to actual MCP server
        
        # Create intent for MCP
        mcp_intent = IntentPacket(
            type=IntentType.QUERY,
            content="Retrieve model context from MCP server",
            context={
                "protocol": "mcp",
                "action": "list_tools"
            },
            priority=IntentPriority.HIGH
        )
        
        print(f"   Created MCP intent: {mcp_intent.id}")
        await client.create_intent(mcp_intent)
        
        # Create UAP packet for MCP
        mcp_packet = UAPContextPacket(
            type=PacketType.INTENT,
            source_protocol=ProtocolType.REST,
            target_protocol=ProtocolType.MCP,
            source_node="uap-api",
            target_node="mcp-server",
            payload=mcp_intent.model_dump(),
            correlation_id=str(mcp_intent.id)
        )
        
        print(f"   UAP packet created for MCP translation")
        print(f"   Source: {mcp_packet.source_protocol.value}")
        print(f"   Target: {mcp_packet.target_protocol.value}")
        
        # Step 2: A2A Bridge Example
        print("\n2. A2A (Agent-to-Agent) Bridge")
        print("-" * 40)
        
        a2a_bridge = A2ABridge({
            "agent_id": "uap-agent-001",
            "peer_agents": []
        })
        
        print("   Initializing A2A bridge...")
        
        # Create intent for A2A
        a2a_intent = IntentPacket(
            type=IntentType.COLLABORATE,
            content="Collaborate with peer agents on optimization task",
            context={
                "protocol": "a2a",
                "collaboration_type": "distributed_optimization",
                "participants": ["agent-001", "agent-002", "agent-003"]
            },
            priority=IntentPriority.HIGH
        )
        
        print(f"   Created A2A intent: {a2a_intent.id}")
        await client.create_intent(a2a_intent)
        
        # Create UAP packet for A2A
        a2a_packet = UAPContextPacket(
            type=PacketType.INTENT,
            source_protocol=ProtocolType.REST,
            target_protocol=ProtocolType.A2A,
            source_node="uap-api",
            target_node="agent-001",
            payload=a2a_intent.model_dump(),
            correlation_id=str(a2a_intent.id)
        )
        
        print(f"   UAP packet created for A2A translation")
        print(f"   Participants: {len(a2a_intent.context['participants'])}")
        
        # Step 3: ACP Bridge Example
        print("\n3. ACP (Agent Communication Protocol) Bridge")
        print("-" * 40)
        
        acp_bridge = ACPBridge({
            "agent_id": "uap-agent-001",
            "api_endpoint": "http://localhost:8080"
        })
        
        print("   Initializing ACP bridge...")
        
        # Create intent for ACP
        acp_intent = IntentPacket(
            type=IntentType.EXECUTE,
            content="Execute action via ACP agent",
            context={
                "protocol": "acp",
                "action": "process_hvac_data",
                "agent_endpoint": "http://localhost:8080/api/agent"
            },
            priority=IntentPriority.HIGH
        )
        
        print(f"   Created ACP intent: {acp_intent.id}")
        await client.create_intent(acp_intent)
        
        # Create UAP packet for ACP
        acp_packet = UAPContextPacket(
            type=PacketType.INTENT,
            source_protocol=ProtocolType.REST,
            target_protocol=ProtocolType.ACP,
            source_node="uap-api",
            target_node="acp-agent",
            payload=acp_intent.model_dump(),
            correlation_id=str(acp_intent.id)
        )
        
        print(f"   UAP packet created for ACP translation")
        print(f"   Action: {acp_intent.context['action']}")
        
        # Step 4: Multi-Protocol Workflow
        print("\n4. Multi-Protocol Workflow")
        print("-" * 40)
        
        print("   Creating cross-protocol action graph...")
        
        # Create nodes for different protocols
        mcp_node = ActionNode(
            type="mcp_query",
            data={
                "protocol": "mcp",
                "action": "get_context",
                "packet": mcp_packet.model_dump()
            }
        )
        
        a2a_node = ActionNode(
            type="a2a_collaborate",
            data={
                "protocol": "a2a",
                "action": "distributed_process",
                "packet": a2a_packet.model_dump()
            }
        )
        
        acp_node = ActionNode(
            type="acp_execute",
            data={
                "protocol": "acp",
                "action": "execute_task",
                "packet": acp_packet.model_dump()
            }
        )
        
        # Create graph with all protocols
        multi_protocol_graph = ActionGraph(
            nodes=[mcp_node, a2a_node, acp_node],
            edges=[
                {"from": str(mcp_node.id), "to": str(a2a_node.id)},
                {"from": str(a2a_node.id), "to": str(acp_node.id)}
            ]
        )
        
        created_graph = await client.create_action_graph(multi_protocol_graph)
        print(f"   Multi-protocol graph created: {created_graph.id}")
        print(f"   Protocols involved: MCP → A2A → ACP")
        
        # Execute the graph
        print("\n   Executing multi-protocol workflow...")
        execution = await client.execute_action_graph(created_graph.id)
        print(f"   Execution status: {execution.get('status')}")
        
        # Step 5: Summary
        print("\n" + "=" * 60)
        print("Protocol Bridge Summary")
        print("=" * 60)
        print("✅ MCP Bridge: Initialized and packet created")
        print("✅ A2A Bridge: Initialized and packet created")
        print("✅ ACP Bridge: Initialized and packet created")
        print("✅ Multi-protocol graph: Created and executed")
        print()
        print("🎉 Protocol bridging demonstration complete!")
        print()
        print("💡 Key Capabilities Demonstrated:")
        print("   - Protocol translation (REST → MCP/A2A/ACP)")
        print("   - Cross-protocol workflows")
        print("   - Unified context packets")
        print("   - Seamless integration across protocols")
        print()


if __name__ == "__main__":
    asyncio.run(protocol_bridge_demo())

