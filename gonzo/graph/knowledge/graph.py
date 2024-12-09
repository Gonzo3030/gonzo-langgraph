from typing import Dict, List, Optional, Any, Iterator, Tuple, Union
from datetime import datetime, UTC
from uuid import UUID
import logging

from .types import Entity, Relationship, TimeAwareEntity, Property

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """High-level interface for managing and analyzing knowledge graphs."""
    
    def __init__(self):
        # Allow either Entity or TimeAwareEntity in the dict
        self._entities: Dict[UUID, Union[Entity, TimeAwareEntity]] = {}
        self._relationships: Dict[UUID, Relationship] = {}
    
    def add_entity(self, 
                   entity_type: str,
                   properties: Dict[str, Any],
                   temporal: bool = False,
                   valid_from: Optional[datetime] = None,
                   valid_to: Optional[datetime] = None) -> Union[Entity, TimeAwareEntity]:
        """Create and add a new entity to the graph."""
        logger.debug(f"Adding entity of type {entity_type} with properties {properties}")
        
        # Create appropriate entity type
        if temporal:
            # Ensure datetimes are UTC-aware
            if valid_from and valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=UTC)
            if valid_to and valid_to.tzinfo is None:
                valid_to = valid_to.replace(tzinfo=UTC)
                
            entity = TimeAwareEntity(
                type=entity_type,
                valid_from=valid_from,
                valid_to=valid_to
            )
            logger.debug(f"Created TimeAwareEntity with valid_from={valid_from}")
        else:
            entity = Entity(type=entity_type)
            
        # Add properties
        for key, value in properties.items():
            entity.add_property(key, value)
            
        # Store in graph
        self._entities[entity.id] = entity
        logger.debug(f"Added entity with ID {entity.id} of type {type(entity)}")
        
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
    
    def get_entity(self, entity_id: UUID) -> Optional[Union[Entity, TimeAwareEntity]]:
        """Retrieve an entity by ID."""
        logger.debug(f"Getting entity with ID {entity_id}")
        entity = self._entities.get(entity_id)
        logger.debug(f"Found entity: {entity} of type {type(entity)}")
        return entity
    
    def get_relationship(self, relationship_id: UUID) -> Optional[Relationship]:
        """Retrieve a relationship by ID."""
        return self._relationships.get(relationship_id)
    
    def get_entity_relationships(self, entity_id: UUID) -> List[Relationship]:
        """Get all relationships where the entity is the source."""
        return [r for r in self._relationships.values() if r.source_id == entity_id]
    
    def get_entities(self,
                    entity_type: Optional[str] = None,
                    valid_from_after: Optional[datetime] = None,
                    valid_to_before: Optional[datetime] = None,
                    property_filters: Optional[List[Tuple[str, Any]]] = None) -> List[Union[Entity, TimeAwareEntity]]:
        """Get entities with optional type, temporal, and property filtering."""
        entities = list(self._entities.values())
        logger.debug(f"Starting with {len(entities)} entities")
        
        if entity_type is not None:
            entities = [e for e in entities if e.type == entity_type]
            logger.debug(f"After type filter: {len(entities)} entities")
            
        if valid_from_after is not None:
            # Ensure comparison datetime is UTC-aware
            if valid_from_after.tzinfo is None:
                valid_from_after = valid_from_after.replace(tzinfo=UTC)
            
            filtered = []
            for e in entities:
                if not isinstance(e, TimeAwareEntity):
                    logger.debug(f"Entity {e.id} is not TimeAwareEntity (type={type(e)})")
                    continue
                if not e.valid_from:
                    logger.debug(f"Entity {e.id} has no valid_from")
                    continue
                if e.valid_from < valid_from_after:
                    logger.debug(f"Entity {e.id} valid_from {e.valid_from} < {valid_from_after}")
                    continue
                filtered.append(e)
                
            entities = filtered
            logger.debug(f"After time filter: {len(entities)} entities")
            
        if valid_to_before is not None:
            # Ensure comparison datetime is UTC-aware
            if valid_to_before.tzinfo is None:
                valid_to_before = valid_to_before.replace(tzinfo=UTC)
                
            entities = [e for e in entities
                       if isinstance(e, TimeAwareEntity) and
                       (e.valid_to is None or e.valid_to <= valid_to_before)]
            
        if property_filters:
            for key, value in property_filters:
                entities = [e for e in entities 
                           if key in e.properties and
                           e.properties[key].value == value]
                
        return entities

    def get_entities_by_type(self, entity_type: str) -> List[Union[Entity, TimeAwareEntity]]:
        """Get all entities of a given type."""
        return self.get_entities(entity_type=entity_type)

    def get_relationships_by_type(self, 
                                 relationship_type: str,
                                 source_id: Optional[UUID] = None) -> List[Relationship]:
        """Get all relationships of a given type, optionally filtered by source."""
        relationships = [r for r in self._relationships.values() 
                       if r.type == relationship_type]
        
        if source_id is not None:
            relationships = [r for r in relationships 
                           if r.source_id == source_id]
            
        return relationships