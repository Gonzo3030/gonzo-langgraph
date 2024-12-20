from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from uuid import UUID, uuid4

@dataclass
class Property:
    """A property represents a key-value pair with temporal metadata."""
    key: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Entity:
    """
    An entity represents a node in the knowledge graph with properties
    and temporal metadata.
    """
    type: str  # Required argument first
    id: UUID = field(default_factory=uuid4)  # Default arguments after
    properties: Dict[str, Property] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_property(self, key: str, value: Any, confidence: float = 1.0, 
                    source: Optional[str] = None) -> None:
        """Add or update a property with temporal tracking."""
        self.properties[key] = Property(
            key=key,
            value=value,
            confidence=confidence,
            source=source
        )
        self.updated_at = datetime.now()

@dataclass
class Relationship:
    """
    A relationship represents a directed edge between entities with
    temporal and causal metadata.
    """
    type: str  # Required arguments first
    source_id: UUID
    target_id: UUID
    id: UUID = field(default_factory=uuid4)  # Default arguments after
    properties: Dict[str, Property] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    causal_strength: Optional[float] = None
    temporal_ordering: Optional[str] = None  # before, after, during, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TimeAwareEntity(Entity):
    """
    An entity that explicitly tracks its temporal existence and changes
    over time.
    """
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    previous_versions: List[Dict[str, Any]] = field(default_factory=list)
    
    def update_property(self, key: str, value: Any, confidence: float = 1.0,
                       source: Optional[str] = None) -> None:
        """Update a property while preserving history."""
        if key in self.properties:
            old_prop = self.properties[key]
            self.previous_versions.append({
                "key": key,
                "value": old_prop.value,
                "confidence": old_prop.confidence,
                "source": old_prop.source,
                "timestamp": old_prop.timestamp
            })
        self.add_property(key, value, confidence, source)