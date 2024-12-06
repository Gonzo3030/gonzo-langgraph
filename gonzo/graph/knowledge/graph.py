from typing import Dict, List, Optional, Any, Iterator, Tuple
from datetime import datetime
from uuid import UUID
import logging

from .types import Entity, Relationship, TimeAwareEntity, Property

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """High-level interface for managing and analyzing knowledge graphs."""
    
    def __init__(self):
        self._entities: Dict[UUID, Entity] = {}
        self._relationships: Dict[UUID, Relationship] = {}
    
    def add_entity(self, 
                   entity_type: str,
                   properties: Dict[str, Any],
                   temporal: bool = False,
                   valid_from: Optional[datetime] = None,
                   valid_to: Optional[datetime] = None) -> Entity:
        """Create and add a new entity to the graph."""
        logger.debug(f"Adding entity of type {entity_type} with properties {properties}")
        
        # Create appropriate entity type
        if temporal:
            entity = TimeAwareEntity(
                type=entity_type,
                valid_from=valid_from,
                valid_to=valid_to
            )
        else:
            entity = Entity(type=entity_type)
            
        # Add properties
        for key, value in properties.items():
            entity.add_property(key, value)
            
        # Store in graph
        self._entities[entity.id] = entity
        logger.debug(f"Added entity with ID {entity.id}")
        
        return entity
    
    def add_relationship(self,
                        relationship_type: str,
                        source_id: UUID,
                        target_id: UUID,
                        properties: Optional[Dict[str, Any]] = None,
                        causal_strength: Optional[float] = None,
                        temporal_ordering: Optional[str] = None) -> Relationship:
        """Create and add a new relationship between entities."""
        logger.debug(f"Adding relationship of type {relationship_type} between {source_id} and {target_id}")
        
        # Verify entities exist
        if source_id not in self._entities or target_id not in self._entities:
            raise ValueError("Both source and target entities must exist")
        
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
                
        self._relationships[relationship.id] = relationship
        logger.debug(f"Added relationship with ID {relationship.id}")
        
        return relationship
    
    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        logger.debug(f"Getting entity with ID {entity_id}")
        entity = self._entities.get(entity_id)
        logger.debug(f"Found entity: {entity}")
        return entity
    
    def get_relationship(self, relationship_id: UUID) -> Optional[Relationship]:
        """Retrieve a relationship by ID."""
        return self._relationships.get(relationship_id)
    
    def get_entity_relationships(self, entity_id: UUID) -> List[Relationship]:
        """Get all relationships where the entity is the source."""
        return [r for r in self._relationships.values() if r.source_id == entity_id]
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a given type."""
        return [e for e in self._entities.values() if e.type == entity_type]