"""Load testing with Locust"""

from __future__ import annotations

import json
from uuid import uuid4
from locust import HttpUser, task, between


class UAPUser(HttpUser):
    """Simulated UAP user for load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    @task(3)
    def create_intent(self):
        """Create intent (weighted: 3)"""
        intent_data = {
            "id": str(uuid4()),
            "type": "action",
            "content": f"Load test intent {uuid4()}",
            "context": {"test": "load"},
            "priority": 1
        }
        
        with self.client.post(
            "/api/v1/intents",
            json=intent_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def get_health(self):
        """Check health (weighted: 2)"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200 and response.json().get("status") == "healthy":
                response.success()
            else:
                response.failure("Health check failed")
    
    @task(1)
    def get_metrics(self):
        """Get metrics (weighted: 1)"""
        self.client.get("/metrics")
    
    @task(2)
    def create_graph(self):
        """Create action graph (weighted: 2)"""
        graph_data = {
            "id": str(uuid4()),
            "nodes": [
                {
                    "id": str(uuid4()),
                    "type": "test",
                    "data": {"test": "load"},
                    "dependencies": []
                }
            ],
            "edges": [],
            "status": "pending"
        }
        
        self.client.post("/api/v1/graphs", json=graph_data)
    
    def on_start(self):
        """Called when a simulated user starts"""
        pass
    
    def on_stop(self):
        """Called when a simulated user stops"""
        pass

