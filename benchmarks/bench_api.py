"""API Performance Benchmarks"""

from __future__ import annotations

import asyncio
import time
from statistics import mean, median, stdev
from typing import List, Dict, Any

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uap.client import AsyncUAPClient
from uap.models.intent import IntentPacket, IntentType, IntentPriority


class APIBenchmark:
    """Benchmark API operations"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: Dict[str, List[float]] = {}
    
    async def benchmark_intent_creation(self, iterations: int = 100) -> Dict[str, float]:
        """Benchmark intent creation"""
        print(f"\n🔬 Benchmarking Intent Creation ({iterations} iterations)...")
        
        timings = []
        
        async with AsyncUAPClient(self.base_url) as client:
            for i in range(iterations):
                intent = IntentPacket(
                    type=IntentType.ACTION,
                    content=f"Benchmark intent {i}",
                    context={"iteration": i},
                    priority=IntentPriority.MEDIUM
                )
                
                start = time.perf_counter()
                await client.create_intent(intent)
                end = time.perf_counter()
                
                timings.append((end - start) * 1000)  # Convert to ms
        
        return self._calculate_stats("intent_creation", timings)
    
    async def benchmark_graph_creation(self, iterations: int = 100) -> Dict[str, float]:
        """Benchmark action graph creation"""
        from src.uap.models.action_graph import ActionGraph, ActionNode
        
        print(f"\n🔬 Benchmarking Action Graph Creation ({iterations} iterations)...")
        
        timings = []
        
        async with AsyncUAPClient(self.base_url) as client:
            for i in range(iterations):
                node = ActionNode(type="test", data={"iteration": i})
                graph = ActionGraph(nodes=[node], edges=[])
                
                start = time.perf_counter()
                await client.create_action_graph(graph)
                end = time.perf_counter()
                
                timings.append((end - start) * 1000)
        
        return self._calculate_stats("graph_creation", timings)
    
    async def benchmark_concurrent_requests(self, concurrent: int = 10, total: int = 100) -> Dict[str, float]:
        """Benchmark concurrent requests"""
        print(f"\n🔬 Benchmarking Concurrent Requests ({concurrent} concurrent, {total} total)...")
        
        timings = []
        
        async def create_intent(client: AsyncUAPClient, i: int):
            intent = IntentPacket(
                type=IntentType.ACTION,
                content=f"Concurrent intent {i}",
                context={"iteration": i},
                priority=IntentPriority.MEDIUM
            )
            
            start = time.perf_counter()
            await client.create_intent(intent)
            end = time.perf_counter()
            
            return (end - start) * 1000
        
        async with AsyncUAPClient(self.base_url) as client:
            for batch_start in range(0, total, concurrent):
                batch_end = min(batch_start + concurrent, total)
                tasks = [
                    create_intent(client, i)
                    for i in range(batch_start, batch_end)
                ]
                
                batch_timings = await asyncio.gather(*tasks)
                timings.extend(batch_timings)
        
        return self._calculate_stats("concurrent_requests", timings)
    
    def _calculate_stats(self, name: str, timings: List[float]) -> Dict[str, float]:
        """Calculate statistics from timings"""
        self.results[name] = timings
        
        stats = {
            "min": min(timings),
            "max": max(timings),
            "mean": mean(timings),
            "median": median(timings),
            "stdev": stdev(timings) if len(timings) > 1 else 0,
            "p95": sorted(timings)[int(len(timings) * 0.95)],
            "p99": sorted(timings)[int(len(timings) * 0.99)],
            "iterations": len(timings)
        }
        
        print(f"   Min:    {stats['min']:.2f}ms")
        print(f"   Max:    {stats['max']:.2f}ms")
        print(f"   Mean:   {stats['mean']:.2f}ms")
        print(f"   Median: {stats['median']:.2f}ms")
        print(f"   P95:    {stats['p95']:.2f}ms")
        print(f"   P99:    {stats['p99']:.2f}ms")
        
        return stats
    
    def generate_report(self) -> str:
        """Generate benchmark report"""
        report = []
        report.append("\n" + "=" * 70)
        report.append("UAP Performance Benchmark Report")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        report.append("")
        
        for name, timings in self.results.items():
            report.append(f"\n{name.replace('_', ' ').title()}:")
            report.append("-" * 70)
            
            stats = self._calculate_stats(name, timings)
            report.append(f"  Operations: {stats['iterations']}")
            report.append(f"  Average:    {stats['mean']:.2f}ms")
            report.append(f"  Median:     {stats['median']:.2f}ms")
            report.append(f"  P95:        {stats['p95']:.2f}ms")
            report.append(f"  P99:        {stats['p99']:.2f}ms")
            report.append(f"  Min/Max:    {stats['min']:.2f}ms / {stats['max']:.2f}ms")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)


async def run_benchmarks():
    """Run all benchmarks"""
    benchmark = APIBenchmark()
    
    try:
        # Run benchmarks
        await benchmark.benchmark_intent_creation(iterations=100)
        await benchmark.benchmark_graph_creation(iterations=100)
        await benchmark.benchmark_concurrent_requests(concurrent=10, total=100)
        
        # Generate report
        report = benchmark.generate_report()
        print(report)
        
        # Save report
        with open("benchmarks/benchmark_report.txt", "w") as f:
            f.write(report)
        
        print("\n✅ Benchmark report saved to: benchmarks/benchmark_report.txt")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        print("   Make sure UAP server is running at http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(run_benchmarks())

