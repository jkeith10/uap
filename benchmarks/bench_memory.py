"""Memory and Storage Performance Benchmarks"""

from __future__ import annotations

import asyncio
import time
from statistics import mean, median
from typing import List

from src.uap.storage.redis_client import RedisClient, RedisConfig
from src.uap.storage.postgres_client import PostgreSQLClient, PostgreSQLConfig


async def benchmark_redis_operations():
    """Benchmark Redis operations"""
    print("\n🔬 Benchmarking Redis Operations...")
    
    config = RedisConfig()
    client = RedisClient(config)
    
    await client.connect()
    
    # Benchmark SET operations
    timings = []
    iterations = 1000
    
    for i in range(iterations):
        start = time.perf_counter()
        await client.set(f"benchmark:key:{i}", f"value_{i}")
        end = time.perf_counter()
        timings.append((end - start) * 1000)
    
    print(f"   SET operations ({iterations} iterations):")
    print(f"      Mean: {mean(timings):.3f}ms")
    print(f"      Median: {median(timings):.3f}ms")
    print(f"      Min/Max: {min(timings):.3f}ms / {max(timings):.3f}ms")
    
    # Benchmark GET operations
    timings = []
    
    for i in range(iterations):
        start = time.perf_counter()
        await client.get(f"benchmark:key:{i}")
        end = time.perf_counter()
        timings.append((end - start) * 1000)
    
    print(f"   GET operations ({iterations} iterations):")
    print(f"      Mean: {mean(timings):.3f}ms")
    print(f"      Median: {median(timings):.3f}ms")
    print(f"      Min/Max: {min(timings):.3f}ms / {max(timings):.3f}ms")
    
    # Cleanup
    keys = await client.keys("benchmark:*")
    if keys:
        await client.delete(*keys)
    
    await client.disconnect()


async def benchmark_postgres_operations():
    """Benchmark PostgreSQL operations"""
    print("\n🔬 Benchmarking PostgreSQL Operations...")
    
    config = PostgreSQLConfig()
    client = PostgreSQLClient(config)
    
    try:
        await client.connect()
        
        # Simple query benchmark
        timings = []
        iterations = 100
        
        for i in range(iterations):
            start = time.perf_counter()
            await client.fetchval("SELECT 1")
            end = time.perf_counter()
            timings.append((end - start) * 1000)
        
        print(f"   Simple queries ({iterations} iterations):")
        print(f"      Mean: {mean(timings):.3f}ms")
        print(f"      Median: {median(timings):.3f}ms")
        print(f"      Min/Max: {min(timings):.3f}ms / {max(timings):.3f}ms")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"   ⚠️  PostgreSQL benchmark skipped: {e}")


async def run_storage_benchmarks():
    """Run all storage benchmarks"""
    print("\n" + "=" * 70)
    print("UAP Storage Performance Benchmarks")
    print("=" * 70)
    
    await benchmark_redis_operations()
    await benchmark_postgres_operations()
    
    print("\n" + "=" * 70)
    print("✅ Storage benchmarks complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_storage_benchmarks())

