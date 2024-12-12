from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass

class EntityType(Enum):
    """Types of entities that can be identified in content"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    NARRATIVE = "narrative"
    PATTERN = "pattern"
    MANIPULATION = "manipulation"
    UNKNOWN = "unknown"

@dataclass
class Property:
    """Property of an entity"""
    key: str
    value: Any

@dataclass
class Relationship:
    """Relationship between entities"""
    source_id: UUID
    target_id: UUID
    type: str
    properties: Dict[str, Property]

@dataclass
class TimeAwareEntity:
    """Entity with temporal awareness"""
    type: EntityType
    id: UUID
    properties: Dict[str, Property]
    valid_from: datetime
    valid_to: Optional[datetime] = None
    relationships: Optional[Dict[str, Relationship]] = None