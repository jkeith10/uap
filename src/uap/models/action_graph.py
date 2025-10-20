"""Action Graph Models"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict


class GraphStatus(str, Enum):
    """Status of action graphs"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionNode(BaseModel):
    """Individual node in an action graph"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "node-1",
                "name": "Lead Capture",
                "type": "data_collection",
                "config": {
                    "source": "crm_api",
                    "fields": ["contact", "lead_score", "source"]
                },
                "timeout": 300,
                "retry_count": 3
            }
        }
    )
    
    id: str = Field(description="Unique node identifier within the graph")
    name: str = Field(description="Human-readable node name")
    type: str = Field(description="Node type (e.g., data_collection, analysis, action)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")
    timeout: Optional[int] = Field(None, description="Timeout in seconds")
    retry_count: int = Field(default=0, description="Number of retries on failure")
    dependencies: Set[str] = Field(default_factory=set, description="Node dependencies")
    
    def add_dependency(self, node_id: str) -> None:
        """Add a dependency to this node"""
        self.dependencies.add(node_id)
    
    def remove_dependency(self, node_id: str) -> None:
        """Remove a dependency from this node"""
        self.dependencies.discard(node_id)


class ActionEdge(BaseModel):
    """Edge connecting two nodes in an action graph"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "from_node": "node-1",
                "to_node": "node-2",
                "condition": "success",
                "data_mapping": {
                    "lead_data": "input_data"
                }
            }
        }
    )
    
    from_node: str = Field(description="Source node ID")
    to_node: str = Field(description="Target node ID")
    condition: str = Field(default="success", description="Condition for edge traversal")
    data_mapping: Dict[str, str] = Field(default_factory=dict, description="Data mapping between nodes")


class ActionGraph(BaseModel):
    """Complete action graph structure"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "HVAC Quote Optimization",
                "description": "Optimize HVAC quoting workflow",
                "status": "draft",
                "nodes": [
                    {
                        "id": "lead-capture",
                        "name": "Lead Capture",
                        "type": "data_collection",
                        "config": {"source": "crm_api"},
                        "dependencies": []
                    },
                    {
                        "id": "estimate-accuracy",
                        "name": "Estimate Accuracy",
                        "type": "analysis",
                        "config": {"model": "pricing_ai"},
                        "dependencies": ["lead-capture"]
                    }
                ],
                "edges": [
                    {
                        "from_node": "lead-capture",
                        "to_node": "estimate-accuracy",
                        "condition": "success"
                    }
                ],
                "created_at": "2024-01-01T10:00:00Z"
            }
        }
    )
    
    id: UUID = Field(default_factory=uuid4, description="Unique graph identifier")
    name: str = Field(description="Graph name")
    description: Optional[str] = Field(None, description="Graph description")
    status: GraphStatus = Field(default=GraphStatus.DRAFT, description="Current graph status")
    nodes: List[ActionNode] = Field(default_factory=list, description="Graph nodes")
    edges: List[ActionEdge] = Field(default_factory=list, description="Graph edges")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def add_node(self, node: ActionNode) -> None:
        """Add a node to the graph"""
        # Check for duplicate node IDs
        if any(n.id == node.id for n in self.nodes):
            raise ValueError(f"Node with ID '{node.id}' already exists")
        self.nodes.append(node)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_edge(self, edge: ActionEdge) -> None:
        """Add an edge to the graph"""
        # Validate that both nodes exist
        node_ids = {n.id for n in self.nodes}
        if edge.from_node not in node_ids:
            raise ValueError(f"Source node '{edge.from_node}' does not exist")
        if edge.to_node not in node_ids:
            raise ValueError(f"Target node '{edge.to_node}' does not exist")
        
        self.edges.append(edge)
        self.updated_at = datetime.now(timezone.utc)
    
    def get_node(self, node_id: str) -> Optional[ActionNode]:
        """Get a node by ID"""
        return next((n for n in self.nodes if n.id == node_id), None)
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """Get all dependencies for a node"""
        node = self.get_node(node_id)
        if not node:
            return []
        return list(node.dependencies)
    
    def validate_graph(self) -> List[str]:
        """Validate the graph structure and return any errors"""
        errors = []
        
        # Check for cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False
            
            visited.add(node_id)
            rec_stack.add(node_id)
            
            # Check all outgoing edges
            for edge in self.edges:
                if edge.from_node == node_id:
                    if has_cycle(edge.to_node):
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        # Check each node for cycles
        for node in self.nodes:
            if has_cycle(node.id):
                errors.append(f"Cycle detected involving node '{node.id}'")
        
        # Check for orphaned nodes
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge.from_node)
            connected_nodes.add(edge.to_node)
        
        for node in self.nodes:
            if node.id not in connected_nodes and len(self.nodes) > 1:
                errors.append(f"Orphaned node '{node.id}' has no connections")
        
        return errors
    
    def to_dag_format(self) -> Dict[str, Any]:
        """Convert to DAG format for execution engines"""
        return {
            "graph_id": str(self.id),
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type,
                    "config": node.config,
                    "timeout": node.timeout,
                    "retry_count": node.retry_count,
                    "dependencies": list(node.dependencies)
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "condition": edge.condition,
                    "data_mapping": edge.data_mapping
                }
                for edge in self.edges
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
