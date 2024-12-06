from typing import Dict, List, Optional, Any, Iterator, Tuple
from datetime import datetime
from uuid import UUID

from .types import Entity, Relationship, TimeAwareEntity, Property
from .store import GraphStore

class KnowledgeGraph:
    """High-level interface for managing and analyzing knowledge graphs."""
    
    def __init__(self):
        self.store = GraphStore()
        
    def add_entity(self, 
                   entity_type: str,
                   properties: Dict[str, Any],
                   temporal: bool = False,
                   valid_from: Optional[datetime] = None,
                   valid_to: Optional[datetime] = None) -> Entity:
        """Create and add a new entity to the graph."""
        if temporal:
            entity = TimeAwareEntity(
                type=entity_type,
                valid_from=valid_from,
                valid_to=valid_to
            )
        else:
            entity = Entity(type=entity_type)
            
        for key, value in properties.items():
            entity.add_property(key, value)
            
        self.store.add_entity(entity)
        return entity
        
    def add_relationship(self,
                        relationship_type: str,
                        source_id: UUID,
                        target_id: UUID,
                        properties: Optional[Dict[str, Any]] = None,
                        causal_strength: Optional[float] = None,
                        temporal_ordering: Optional[str] = None) -> Relationship:
        """Create and add a new relationship between entities."""
        relationship = Relationship(
            type=relationship_type,
            source_id=source_id,
            target_id=target_id,
            causal_strength=causal_strength,
            temporal_ordering=temporal_ordering
        )
        
        if properties:
            for key, value in properties.items():
                relationship.properties[key] = Property(key=key, value=value)
                
        self.store.add_relationship(relationship)
        return relationship
        
    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self.store.get_entity(entity_id)
        
    def get_relationships(self, entity_id: UUID) -> List[Relationship]:
        """Get all relationships where the entity is the source."""
        return self.store.get_relationships(entity_id)
