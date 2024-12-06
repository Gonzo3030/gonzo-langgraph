from typing import Dict, List, Optional, Set, Any, Iterator
from datetime import datetime
from uuid import UUID
from .types import Entity, Relationship, Property

class GraphStore:
    """Base class for graph storage implementations."""
    
    def __init__(self):
        self._entities: Dict[UUID, Entity] = {}
        self._relationships: Dict[UUID, Relationship] = {}
        self._entity_relationships: Dict[UUID, Set[UUID]] = {}
        self._type_indices: Dict[str, Set[UUID]] = {}
        
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the graph."""
        self._entities[entity.id] = entity
        if entity.type not in self._type_indices:
            self._type_indices[entity.type] = set()
        self._type_indices[entity.type].add(entity.id)
        self._entity_relationships[entity.id] = set()
        
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship between entities."""
        if relationship.source_id not in self._entities or \
           relationship.target_id not in self._entities:
            raise ValueError("Both source and target entities must exist")
            
        self._relationships[relationship.id] = relationship
        self._entity_relationships[relationship.source_id].add(relationship.id)
        
    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self._entities.get(entity_id)
        
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Retrieve all entities of a given type."""
        entity_ids = self._type_indices.get(entity_type, set())
        return [self._entities[eid] for eid in entity_ids]
        
    def get_relationships(self, entity_id: UUID) -> List[Relationship]:
        """Get all relationships where the entity is the source."""
        rel_ids = self._entity_relationships.get(entity_id, set())
        return [self._relationships[rid] for rid in rel_ids]
        
    def query_entities(self, 
                      entity_type: Optional[str] = None,
                      properties: Optional[Dict[str, Any]] = None,
                      timestamp: Optional[datetime] = None) -> Iterator[Entity]:
        """Query entities with optional type, property, and temporal filters."""
        entities = self._entities.values()
        
        if entity_type:
            type_ids = self._type_indices.get(entity_type, set())
            entities = [e for e in entities if e.id in type_ids]
            
        if properties:
            entities = [
                e for e in entities
                if all(k in e.properties and e.properties[k].value == v 
                      for k, v in properties.items())
            ]
            
        if timestamp:
            entities = [
                e for e in entities
                if hasattr(e, 'is_valid_at') and e.is_valid_at(timestamp)
            ]
            
        yield from entities
        
    def find_paths(self,
                   start_id: UUID,
                   end_id: UUID,
                   max_depth: int = 5) -> List[List[UUID]]:
        """Find all paths between two entities up to a maximum depth."""
        paths: List[List[UUID]] = []
        visited = set()
        
        def dfs(current_id: UUID, path: List[UUID], depth: int) -> None:
            if depth > max_depth or current_id in visited:
                return
                
            visited.add(current_id)
            path.append(current_id)
            
            if current_id == end_id:
                paths.append(path.copy())
            else:
                for rel_id in self._entity_relationships.get(current_id, set()):
                    rel = self._relationships[rel_id]
                    dfs(rel.target_id, path, depth + 1)
                    
            path.pop()
            visited.remove(current_id)
            
        dfs(start_id, [], 0)
        return paths
        
    def get_causal_chain(self,
                        entity_id: UUID,
                        max_depth: int = 5,
                        min_confidence: float = 0.5) -> List[List[UUID]]:
        """Find causal chains starting from an entity."""
        chains: List[List[UUID]] = []
        visited = set()
        
        def dfs(current_id: UUID, chain: List[UUID], depth: int) -> None:
            if depth > max_depth or current_id in visited:
                return
                
            visited.add(current_id)
            chain.append(current_id)
            
            for rel_id in self._entity_relationships.get(current_id, set()):
                rel = self._relationships[rel_id]
                if rel.causal_strength and rel.causal_strength >= min_confidence:
                    dfs(rel.target_id, chain, depth + 1)
                    
            if len(chain) > 1:
                chains.append(chain.copy())
                
            chain.pop()
            visited.remove(current_id)
            
        dfs(entity_id, [], 0)
        return chains