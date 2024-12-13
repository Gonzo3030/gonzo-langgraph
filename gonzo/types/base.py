"""Base type definitions for Gonzo system."""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass

class EntityType(Enum):
    """Types of entities that can be identified in content."""
    PERSON = "person"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    EVENT = "event"
    TECHNOLOGY = "technology"
    PATTERN = "pattern"
    MANIPULATION = "manipulation"
    NARRATIVE = "narrative"
    RESISTANCE = "resistance"
    UNKNOWN = "unknown"

@dataclass
class Property:
    """Property of an entity."""
    key: str
    value: Any

@dataclass
class Relationship:
    """Relationship between entities."""
    source_id: UUID
    target_id: UUID
    type: str
    properties: Dict[str, Property]

@dataclass
class TimeAwareEntity:
    """Entity with temporal awareness."""
    type: EntityType
    id: UUID
    properties: Dict[str, Property]
    valid_from: datetime
    valid_to: Optional[datetime] = None
    relationships: Optional[Dict[str, Relationship]] = None