"""Contextual pattern detection with dynamic knowledge updating."""

from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, UTC
from uuid import UUID
import logging
from enum import Enum

from ..memory.vector_store import VectorStoreMemory
from ..memory.timeline import Timeline
from ..persistence.checkpointer import Checkpointer
from ..persistence.store import Store
from ..state_management.api_state import APIState

logger = logging.getLogger(__name__)

class ConfidenceLevel(float, Enum):
    """Confidence levels for knowledge claims."""
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.9

class KnowledgeClaim:
    """Represents a piece of knowledge with source and confidence."""
    
    def __init__(self, 
        value: Any,
        source: str,
        confidence: float,
        timestamp: datetime = None
    ):
        self.value = value
        self.source = source
        self.confidence = confidence
        self.timestamp = timestamp or datetime.now(UTC)
        self.corroborations: List[Tuple[str, float]] = []  # (source, confidence)
        
    def add_corroboration(self, source: str, confidence: float) -> None:
        """Add a corroborating source."""
        self.corroborations.append((source, confidence))
        # Update overall confidence based on corroboration
        max_boost = 0.1 * len(self.corroborations)  # Max 10% boost per corroboration
        self.confidence = min(1.0, self.confidence + max_boost)
        
    def to_memory_entry(self) -> Dict[str, Any]:
        """Convert to format suitable for vector store."""
        return {
            "text": str(self.value),
            "metadata": {
                "source": self.source,
                "confidence": self.confidence,
                "timestamp": self.timestamp,
                "corroborations": self.corroborations
            }
        }

class Entity:
    """Represents an entity in the power structure."""
    
    def __init__(self, 
        id: str,
        name: str,
        entity_type: str,
        properties: Dict[str, Any] = None
    ):
        self.id = id
        self.name = name
        self.entity_type = entity_type
        self.properties: Dict[str, KnowledgeClaim] = {}
        self.relationships: Dict[str, Dict[str, KnowledgeClaim]] = {
            "supports": {},
            "opposes": {},
            "controls": {},
            "influences": {},
            "threatens": {},
            "criticized_by": {}
        }
        self.temporal_context: Dict[str, datetime] = {}
        
        if properties:
            for key, value in properties.items():
                if isinstance(value, KnowledgeClaim):
                    self.properties[key] = value
                else:
                    self.properties[key] = KnowledgeClaim(
                        value=value,
                        source="initial_data",
                        confidence=ConfidenceLevel.MEDIUM
                    )
    
    def update_property(self, 
        key: str,
        value: Any,
        source: str,
        confidence: float
    ) -> None:
        """Update or add a property with new information."""
        if key in self.properties:
            existing = self.properties[key]
            if confidence > existing.confidence:
                # New information is more confident
                self.properties[key] = KnowledgeClaim(value, source, confidence)
            else:
                # Add as corroboration
                existing.add_corroboration(source, confidence)
        else:
            self.properties[key] = KnowledgeClaim(value, source, confidence)
            
class PowerStructure:
    """Tracks power relationships between entities."""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.influence_networks: Dict[str, Dict[str, float]] = {}
        self.financial_relationships: Dict[str, Dict[str, KnowledgeClaim]] = {}
        self.policy_alignments: Dict[str, Dict[str, float]] = {}
        
        self.entity_types = {
            "individual": {
                "properties": ["role", "affiliation", "platform", "net_worth", "connections"]
            },
            "organization": {
                "properties": ["industry", "type", "market_cap", "funding_sources", "political_donations"]
            },
            "media_outlet": {
                "properties": ["type", "parent_company", "bias", "advertisers", "reach"]
            },
            "government": {
                "properties": ["level", "jurisdiction", "party", "donors", "voting_record"]
            }
        }
