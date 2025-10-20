"""Semantic Versioning System for UAP"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class VersionType(str, Enum):
    """Types of versioned objects in UAP"""
    PROMPT = "prompt"
    OBJECTIVE = "objective"
    OUTCOME = "outcome"
    SCHEMA = "schema"
    PROTOCOL = "protocol"
    AGENT = "agent"


@dataclass
class SemanticVersion:
    """Semantic version representation"""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        """Parse a semantic version string"""
        # Regex pattern for semantic versioning
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
        match = re.match(pattern, version_str)
        
        if not match:
            raise ValueError(f"Invalid semantic version: {version_str}")
        
        major, minor, patch, prerelease, build = match.groups()
        
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build=build
        )
    
    def __lt__(self, other: "SemanticVersion") -> bool:
        """Compare versions for ordering"""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        
        # Compare major, minor, patch
        if (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch):
            return True
        if (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch):
            return False
        
        # Compare prerelease
        if self.prerelease is None and other.prerelease is not None:
            return False  # Stable version is greater than prerelease
        if self.prerelease is not None and other.prerelease is None:
            return True   # Prerelease is less than stable version
        if self.prerelease is not None and other.prerelease is not None:
            return self.prerelease < other.prerelease
        
        return False
    
    def __eq__(self, other: "SemanticVersion") -> bool:
        """Check if versions are equal"""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )
    
    def __le__(self, other: "SemanticVersion") -> bool:
        return self < other or self == other
    
    def __gt__(self, other: "SemanticVersion") -> bool:
        return not self <= other
    
    def __ge__(self, other: "SemanticVersion") -> bool:
        return not self < other
    
    def is_compatible_with(self, other: "SemanticVersion") -> bool:
        """Check if this version is compatible with another (same major version)"""
        return self.major == other.major
    
    def next_major(self) -> "SemanticVersion":
        """Get next major version"""
        return SemanticVersion(self.major + 1, 0, 0)
    
    def next_minor(self) -> "SemanticVersion":
        """Get next minor version"""
        return SemanticVersion(self.major, self.minor + 1, 0)
    
    def next_patch(self) -> "SemanticVersion":
        """Get next patch version"""
        return SemanticVersion(self.major, self.minor, self.patch + 1)


class VersionedObject(BaseModel):
    """Base class for versioned objects in UAP"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "prompt-001",
                "type": "prompt",
                "version": "1.2.3",
                "content": "Optimize the HVAC pricing strategy...",
                "metadata": {
                    "author": "system",
                    "domain": "hvac"
                },
                "created_at": "2024-01-01T10:00:00Z"
            }
        }
    )
    
    id: str = Field(description="Unique identifier for the versioned object")
    type: VersionType = Field(description="Type of versioned object")
    version: str = Field(description="Semantic version string")
    content: Any = Field(description="The actual content being versioned")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        """Validate that version is a valid semantic version"""
        try:
            SemanticVersion.parse(v)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid semantic version: {e}")
    
    def get_semantic_version(self) -> SemanticVersion:
        """Get the semantic version object"""
        return SemanticVersion.parse(self.version)
    
    def is_compatible_with(self, other: "VersionedObject") -> bool:
        """Check if this object is compatible with another version"""
        return self.get_semantic_version().is_compatible_with(other.get_semantic_version())


class VersionManager:
    """Manages versioning of UAP objects"""
    
    def __init__(self):
        self._versions: Dict[str, List[VersionedObject]] = {}
        self._latest: Dict[str, VersionedObject] = {}
    
    def register_version(self, obj: VersionedObject) -> None:
        """Register a new version of an object"""
        if obj.id not in self._versions:
            self._versions[obj.id] = []
        
        # Check if version already exists
        existing_versions = [v.version for v in self._versions[obj.id]]
        if obj.version in existing_versions:
            raise ValueError(f"Version {obj.version} already exists for {obj.id}")
        
        # Add to versions list
        self._versions[obj.id].append(obj)
        
        # Sort by version
        self._versions[obj.id].sort(key=lambda x: x.get_semantic_version())
        
        # Update latest version
        self._latest[obj.id] = self._versions[obj.id][-1]
    
    def get_latest_version(self, obj_id: str) -> Optional[VersionedObject]:
        """Get the latest version of an object"""
        return self._latest.get(obj_id)
    
    def get_version(self, obj_id: str, version: str) -> Optional[VersionedObject]:
        """Get a specific version of an object"""
        if obj_id not in self._versions:
            return None
        
        for obj in self._versions[obj_id]:
            if obj.version == version:
                return obj
        
        return None
    
    def get_all_versions(self, obj_id: str) -> List[VersionedObject]:
        """Get all versions of an object"""
        return self._versions.get(obj_id, [])
    
    def get_compatible_versions(
        self,
        obj_id: str,
        target_version: str
    ) -> List[VersionedObject]:
        """Get all versions compatible with a target version"""
        if obj_id not in self._versions:
            return []
        
        target_semver = SemanticVersion.parse(target_version)
        compatible = []
        
        for obj in self._versions[obj_id]:
            if obj.get_semantic_version().is_compatible_with(target_semver):
                compatible.append(obj)
        
        return compatible
    
    def suggest_next_version(
        self,
        obj_id: str,
        change_type: str = "patch"
    ) -> str:
        """Suggest the next version for an object"""
        latest = self.get_latest_version(obj_id)
        if not latest:
            return "1.0.0"
        
        current_semver = latest.get_semantic_version()
        
        if change_type == "major":
            return str(current_semver.next_major())
        elif change_type == "minor":
            return str(current_semver.next_minor())
        else:  # patch
            return str(current_semver.next_patch())
    
    def migrate_object(
        self,
        obj: VersionedObject,
        target_version: str
    ) -> Optional[VersionedObject]:
        """Migrate an object to a target version"""
        target_obj = self.get_version(obj.id, target_version)
        if not target_obj:
            return None
        
        # Check compatibility
        if not obj.is_compatible_with(target_obj):
            # In a real implementation, you'd have migration logic here
            # For now, we'll just return the target object
            pass
        
        return target_obj
    
    def list_objects(self) -> List[str]:
        """List all object IDs"""
        return list(self._versions.keys())
    
    def get_version_history(self, obj_id: str) -> List[Tuple[str, str]]:
        """Get version history for an object"""
        if obj_id not in self._versions:
            return []
        
        return [(obj.version, obj.created_at or "unknown") for obj in self._versions[obj_id]]


class VersionMigration:
    """Handles migration between versions"""
    
    def __init__(self):
        self._migrations: Dict[Tuple[str, str], callable] = {}
    
    def register_migration(
        self,
        from_version: str,
        to_version: str,
        migration_func: callable
    ) -> None:
        """Register a migration function between versions"""
        key = (from_version, to_version)
        self._migrations[key] = migration_func
    
    def migrate(
        self,
        obj: VersionedObject,
        target_version: str
    ) -> Optional[VersionedObject]:
        """Migrate an object to a target version"""
        current_version = obj.version
        
        if current_version == target_version:
            return obj
        
        # Check if direct migration exists
        key = (current_version, target_version)
        if key in self._migrations:
            return self._migrations[key](obj)
        
        # Try to find a migration path
        # This is a simplified implementation - in practice, you'd want
        # a more sophisticated pathfinding algorithm
        return None
