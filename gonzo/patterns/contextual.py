"""Contextual pattern detection with entity relationship tracking."""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime, UTC
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

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
        self.properties = properties or {}
        self.relationships: Dict[str, List[str]] = {
            "supports": [],
            "opposes": [],
            "controls": [],
            "influences": [],
            "threatens": [],
            "criticized_by": []
        }
        self.temporal_context: Dict[str, datetime] = {}
        
    def add_relationship(self, relationship_type: str, target_id: str) -> None:
        """Add a relationship to another entity."""
        if relationship_type in self.relationships:
            if target_id not in self.relationships[relationship_type]:
                self.relationships[relationship_type].append(target_id)
                
    def add_temporal_context(self, context_type: str, timestamp: datetime) -> None:
        """Add temporal context to the entity."""
        self.temporal_context[context_type] = timestamp

class PowerStructure:
    """Tracks power relationships between entities."""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.entity_types = {
            "individual": {
                "properties": ["role", "affiliation", "platform"]
            },
            "organization": {
                "properties": ["industry", "type", "market_cap"]
            },
            "media_outlet": {
                "properties": ["type", "parent_company", "bias"]
            },
            "government": {
                "properties": ["level", "jurisdiction", "party"]
            }
        }
        
    def add_entity(self, 
        id: str,
        name: str,
        entity_type: str,
        properties: Dict[str, Any] = None
    ) -> Optional[Entity]:
        """Add a new entity to the power structure."""
        if entity_type not in self.entity_types:
            logger.error(f"Invalid entity type: {entity_type}")
            return None
            
        entity = Entity(id, name, entity_type, properties)
        self.entities[id] = entity
        return entity
        
    def add_relationship(self,
        source_id: str,
        target_id: str,
        relationship_type: str
    ) -> bool:
        """Add a relationship between entities."""
        if source_id not in self.entities or target_id not in self.entities:
            return False
            
        self.entities[source_id].add_relationship(relationship_type, target_id)
        return True
        
    def get_related_entities(self,
        entity_id: str,
        relationship_type: Optional[str] = None
    ) -> List[Entity]:
        """Get entities related to the given entity."""
        if entity_id not in self.entities:
            return []
            
        entity = self.entities[entity_id]
        if relationship_type:
            if relationship_type not in entity.relationships:
                return []
            related_ids = entity.relationships[relationship_type]
        else:
            # Get all related entities across all relationship types
            related_ids = set()
            for rel_ids in entity.relationships.values():
                related_ids.update(rel_ids)
                
        return [self.entities[rid] for rid in related_ids if rid in self.entities]

class ContextualPatternDetector:
    """Detects manipulation patterns using contextual awareness."""
    
    def __init__(self):
        self.power_structure = PowerStructure()
        
    def initialize_knowledge_base(self):
        """Initialize basic knowledge of key entities and relationships."""
        # Add key individuals
        self.power_structure.add_entity(
            "rfk_jr",
            "Robert F. Kennedy Jr.",
            "individual",
            {
                "role": "presidential_candidate",
                "platform": ["health_advocacy", "environmental_protection"],
                "affiliation": "democratic_party"
            }
        )
        
        self.power_structure.add_entity(
            "kimmel",
            "Jimmy Kimmel",
            "individual",
            {
                "role": "media_personality",
                "platform": "late_night_show",
                "affiliation": "abc_network"
            }
        )
        
        # Add organizations
        self.power_structure.add_entity(
            "abc",
            "ABC Network",
            "media_outlet",
            {
                "type": "broadcast_network",
                "parent_company": "disney",
                "bias": "mainstream"
            }
        )
        
        self.power_structure.add_entity(
            "big_pharma",
            "Pharmaceutical Industry",
            "organization",
            {
                "industry": "healthcare",
                "type": "industry_group",
                "market_cap": "high"
            }
        )
        
        # Add relationships
        self.power_structure.add_relationship("rfk_jr", "big_pharma", "opposes")
        self.power_structure.add_relationship("big_pharma", "rfk_jr", "criticized_by")
        self.power_structure.add_relationship("kimmel", "abc", "controlled_by")
        self.power_structure.add_relationship("abc", "big_pharma", "influenced_by")
        
    def analyze_narrative_context(self,
        text: str,
        entities: List[str]
    ) -> Dict[str, Any]:
        """Analyze narrative in context of known entity relationships.
        
        Args:
            text: Text to analyze
            entities: List of entity IDs mentioned in the text
            
        Returns:
            Analysis of potential manipulation based on context
        """
        analysis = {
            "type": "contextual_pattern",
            "entities_involved": [],
            "relationships_relevant": [],
            "manipulation_indicators": []
        }
        
        for entity_id in entities:
            if entity_id not in self.power_structure.entities:
                continue
                
            entity = self.power_structure.entities[entity_id]
            analysis["entities_involved"].append({
                "id": entity_id,
                "name": entity.name,
                "type": entity.entity_type
            })
            
            # Get related entities
            related = self.power_structure.get_related_entities(entity_id)
            for rel_entity in related:
                relationship_info = {
                    "source": entity.name,
                    "target": rel_entity.name,
                    "types": []
                }
                
                for rel_type, targets in entity.relationships.items():
                    if rel_entity.id in targets:
                        relationship_info["types"].append(rel_type)
                        
                if relationship_info["types"]:
                    analysis["relationships_relevant"].append(relationship_info)
        
        return analysis