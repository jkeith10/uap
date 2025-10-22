"""Batch Processing Example for UAP"""

from __future__ import annotations

import asyncio
from typing import List, Dict, Any
from uuid import UUID

from src.uap.client import AsyncUAPClient
from src.uap.models.intent import IntentPacket, IntentType, IntentPriority
from src.uap.models.action_graph import ActionGraph, ActionNode
from src.uap.models.memory_stream import MemoryStream, MemoryEntry, MemoryGranularity


async def process_batch_intents(
    client: AsyncUAPClient,
    intents: List[IntentPacket],
    batch_size: int = 10
) -> List[IntentPacket]:
    """Process intents in batches"""
    
    results = []
    total = len(intents)
    
    print(f"Processing {total} intents in batches of {batch_size}...")
    
    for i in range(0, total, batch_size):
        batch = intents[i:i + batch_size]
        print(f"\nBatch {i//batch_size + 1}: Processing {len(batch)} intents...")
        
        # Process batch concurrently
        tasks = [client.create_intent(intent) for intent in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        successful = [r for r in batch_results if not isinstance(r, Exception)]
        failed = [r for r in batch_results if isinstance(r, Exception)]
        
        print(f"   ✅ Success: {len(successful)}")
        if failed:
            print(f"   ❌ Failed: {len(failed)}")
        
        results.extend(successful)
        
        # Small delay between batches
        if i + batch_size < total:
            await asyncio.sleep(0.1)
    
    return results


async def batch_workflow():
    """Demonstrate batch processing workflow"""
    
    print("=" * 60)
    print("UAP Batch Processing Example")
    print("=" * 60)
    print()
    
    async with AsyncUAPClient("http://localhost:8000") as client:
        
        # Step 1: Generate batch of intents
        print("1. Generating batch of intents...")
        
        intents = []
        rooms = ["room_a", "room_b", "room_c", "room_d", "room_e"]
        
        for i in range(50):
            room = rooms[i % len(rooms)]
            temp = 70 + (i % 10)
            
            intent = IntentPacket(
                type=IntentType.ACTION,
                content=f"Adjust temperature in {room} to {temp}°F",
                context={
                    "room": room,
                    "target_temp": temp,
                    "current_temp": temp + 5,
                    "batch_id": "batch-001",
                    "item_number": i + 1
                },
                priority=IntentPriority.MEDIUM
            )
            
            intents.append(intent)
        
        print(f"   Generated {len(intents)} intents")
        
        # Step 2: Process in batches
        print("\n2. Processing intents in batches...")
        results = await process_batch_intents(client, intents, batch_size=10)
        
        # Step 3: Create batch action graph
        print("\n3. Creating batch execution graph...")
        
        nodes = []
        for i in range(5):
            node = ActionNode(
                type="batch_process",
                data={
                    "room": rooms[i],
                    "batch_size": 10,
                    "parallel": True
                }
            )
            nodes.append(node)
        
        # All nodes run in parallel (no edges)
        graph = ActionGraph(nodes=nodes, edges=[])
        
        created_graph = await client.create_action_graph(graph)
        print(f"   Parallel graph created: {created_graph.id}")
        
        # Step 4: Execute batch graph
        print("\n4. Executing batch graph...")
        execution = await client.execute_action_graph(created_graph.id)
        print(f"   Status: {execution.get('status')}")
        
        # Step 5: Aggregate results
        print("\n5. Aggregating results...")
        
        # Group by room
        by_room = {}
        for intent in results:
            room = intent.context.get("room")
            if room not in by_room:
                by_room[room] = []
            by_room[room].append(intent)
        
        print("\n   Results by room:")
        for room, room_intents in by_room.items():
            print(f"   - {room}: {len(room_intents)} intents processed")
        
        # Step 6: Create summary memory
        print("\n6. Creating batch summary memory...")
        
        summary_entry = MemoryEntry(
            type="batch_summary",
            data={
                "total_intents": len(results),
                "by_room": {room: len(items) for room, items in by_room.items()},
                "batch_id": "batch-001",
                "execution_time": "~5 seconds",
                "success_rate": len(results) / len(intents) * 100
            }
        )
        
        summary_memory = MemoryStream(
            granularity=MemoryGranularity.TASK,
            entries=[summary_entry]
        )
        
        created_summary = await client.create_memory_stream(summary_memory)
        print(f"   Summary memory created: {created_summary.id}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("Batch Processing Summary")
        print("=" * 60)
        print(f"✅ Total intents: {len(intents)}")
        print(f"✅ Successfully processed: {len(results)}")
        print(f"✅ Success rate: {len(results)/len(intents)*100:.1f}%")
        print(f"✅ Rooms processed: {len(by_room)}")
        print(f"✅ Parallel nodes: {len(nodes)}")
        print()
        print("🎉 Batch workflow completed successfully!")
        print()


if __name__ == "__main__":
    asyncio.run(batch_workflow())

