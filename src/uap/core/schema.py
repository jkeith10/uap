"""JSON-LD Schema Definitions for UAP"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UAPContext(BaseModel):
    """UAP JSON-LD context definition"""
    
    @staticmethod
    def get_base_context() -> Dict[str, Any]:
        """Get the base UAP JSON-LD context"""
        return {
            "@context": {
                "@vocab": "https://uap.dev/schema#",
                "uap": "https://uap.dev/schema#",
                "schema": "https://schema.org/",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "owl": "http://www.w3.org/2002/07/owl#",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                
                # UAP Core Types
                "IntentPacket": "uap:IntentPacket",
                "ActionGraph": "uap:ActionGraph",
                "ActionNode": "uap:ActionNode",
                "ActionEdge": "uap:ActionEdge",
                "MemoryStream": "uap:MemoryStream",
                "ReflectionReport": "uap:ReflectionReport",
                "EvaluationResult": "uap:EvaluationResult",
                
                # UAP Properties
                "type": "uap:type",
                "goal": "uap:goal",
                "contextRef": "uap:contextRef",
                "priority": "uap:priority",
                "deadline": "uap:deadline",
                "metadata": "uap:metadata",
                "createdAt": "uap:createdAt",
                "updatedAt": "uap:updatedAt",
                "actor": "uap:actor",
                "intent": "uap:intent",
                "context": "uap:context",
                "result": "uap:result",
                "confidence": "uap:confidence",
                "nextAction": "uap:nextAction",
                "granularity": "uap:granularity",
                "retentionPolicy": "uap:retentionPolicy",
                "streamId": "uap:streamId",
                "reportId": "uap:reportId",
                "evaluation": "uap:evaluation",
                "recommendations": "uap:recommendations",
                "score": "uap:score",
                "metrics": "uap:metrics",
                "feedback": "uap:feedback",
                
                # Intent Types
                "IntentType": {
                    "@id": "uap:IntentType",
                    "@type": "@vocab"
                },
                "optimize": "uap:optimize",
                "analyze": "uap:analyze",
                "execute": "uap:execute",
                "collaborate": "uap:collaborate",
                "reflect": "uap:reflect",
                "route": "uap:route",
                "memorize": "uap:memorize",
                "query": "uap:query",
                
                # Graph Status
                "GraphStatus": {
                    "@id": "uap:GraphStatus",
                    "@type": "@vocab"
                },
                "draft": "uap:draft",
                "active": "uap:active",
                "paused": "uap:paused",
                "completed": "uap:completed",
                "failed": "uap:failed",
                "cancelled": "uap:cancelled",
                
                # Memory Granularity
                "MemoryGranularity": {
                    "@id": "uap:MemoryGranularity",
                    "@type": "@vocab"
                },
                "task": "uap:task",
                "agent": "uap:agent",
                "organization": "uap:organization",
                
                # Retention Policy
                "RetentionPolicy": {
                    "@id": "uap:RetentionPolicy",
                    "@type": "@vocab"
                },
                "ephemeral": "uap:ephemeral",
                "archived": "uap:archived",
                "permanent": "uap:permanent"
            }
        }


class UAPSchemaValidator:
    """Validator for UAP JSON-LD schemas"""
    
    @staticmethod
    def validate_intent_packet(data: Dict[str, Any]) -> List[str]:
        """Validate an intent packet against UAP schema"""
        errors = []
        
        if "@type" not in data or data["@type"] != "uap:IntentPacket":
            errors.append("Missing or invalid @type for IntentPacket")
        
        required_fields = ["uap:type", "uap:goal", "uap:priority", "uap:createdAt"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "uap:priority" in data:
            priority = data["uap:priority"]
            if not isinstance(priority, (int, float)) or not (0.0 <= priority <= 1.0):
                errors.append("uap:priority must be a number between 0.0 and 1.0")
        
        return errors
    
    @staticmethod
    def validate_memory_stream(data: Dict[str, Any]) -> List[str]:
        """Validate a memory stream against UAP schema"""
        errors = []
        
        if "@type" not in data or data["@type"] != "uap:MemoryStream":
            errors.append("Missing or invalid @type for MemoryStream")
        
        required_fields = ["uap:streamId", "uap:actor", "uap:intent", "uap:granularity", "uap:retentionPolicy", "uap:createdAt"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "uap:confidence" in data:
            confidence = data["uap:confidence"]
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                errors.append("uap:confidence must be a number between 0.0 and 1.0")
        
        valid_granularities = ["uap:task", "uap:agent", "uap:organization"]
        if "uap:granularity" in data and data["uap:granularity"] not in valid_granularities:
            errors.append(f"uap:granularity must be one of: {valid_granularities}")
        
        valid_retention_policies = ["uap:ephemeral", "uap:archived", "uap:permanent"]
        if "uap:retentionPolicy" in data and data["uap:retentionPolicy"] not in valid_retention_policies:
            errors.append(f"uap:retentionPolicy must be one of: {valid_retention_policies}")
        
        return errors
    
    @staticmethod
    def validate_reflection_report(data: Dict[str, Any]) -> List[str]:
        """Validate a reflection report against UAP schema"""
        errors = []
        
        if "@type" not in data or data["@type"] != "uap:ReflectionReport":
            errors.append("Missing or invalid @type for ReflectionReport")
        
        required_fields = ["uap:reportId", "uap:actor", "uap:intent", "uap:evaluation", "uap:createdAt"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "uap:evaluation" in data:
            evaluation = data["uap:evaluation"]
            if "uap:score" not in evaluation:
                errors.append("uap:evaluation must contain uap:score")
            elif not isinstance(evaluation["uap:score"], (int, float)) or not (0.0 <= evaluation["uap:score"] <= 1.0):
                errors.append("uap:evaluation.uap:score must be a number between 0.0 and 1.0")
        
        return errors


class SchemaRegistry:
    """Registry for UAP schemas and their versions"""
    
    def __init__(self):
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._versions: Dict[str, List[str]] = {}
    
    def register_schema(self, name: str, version: str, schema: Dict[str, Any]) -> None:
        """Register a schema with a specific version"""
        key = f"{name}:{version}"
        self._schemas[key] = schema
        
        if name not in self._versions:
            self._versions[name] = []
        if version not in self._versions[name]:
            self._versions[name].append(version)
            self._versions[name].sort()  # Keep versions sorted
    
    def get_schema(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a schema by name and version"""
        if version is None:
            # Get the latest version
            if name not in self._versions or not self._versions[name]:
                return None
            version = self._versions[name][-1]
        
        key = f"{name}:{version}"
        return self._schemas.get(key)
    
    def get_available_versions(self, name: str) -> List[str]:
        """Get all available versions for a schema"""
        return self._versions.get(name, [])
    
    def list_schemas(self) -> List[str]:
        """List all registered schema names"""
        return list(self._versions.keys())


# Global schema registry instance
schema_registry = SchemaRegistry()

# Register core UAP schemas
schema_registry.register_schema(
    "uap-core",
    "1.0",
    UAPContext.get_base_context()
)
