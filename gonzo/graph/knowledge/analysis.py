from typing import Dict, List, Optional, Any, Iterator, Tuple
from datetime import datetime
from uuid import UUID

from .types import Entity, TimeAwareEntity
from .store import GraphStore

class KnowledgeAnalysis:
    """Analysis capabilities for the knowledge graph."""
    
    def __init__(self, store: GraphStore):
        self.store = store

    def get_entity_by_properties(self,
                                entity_type: str,
                                properties: Dict[str, Any],
                                timestamp: Optional[datetime] = None) -> Optional[Entity]:
        """Find an entity by its type and properties."""
        entities = self.store.query_entities(
            entity_type=entity_type,
            properties=properties,
            timestamp=timestamp
        )
        return next(entities, None)

    def analyze_temporal_patterns(self,
                                entity_type: str,
                                property_key: str,
                                time_window: Tuple[datetime, datetime]) -> List[Dict[str, Any]]:
        """Analyze patterns in property values over time."""
        entities = self.store.query_entities(entity_type=entity_type)
        patterns = []
        
        for entity in entities:
            if isinstance(entity, TimeAwareEntity):
                history = []
                # Gather historical values
                for version in entity.previous_versions:
                    if version['key'] == property_key:
                        history.append({
                            'value': version['value'],
                            'timestamp': version['timestamp']
                        })
                
                # Add current value if it exists
                if property_key in entity.properties:
                    current = entity.properties[property_key]
                    history.append({
                        'value': current.value,
                        'timestamp': current.timestamp
                    })
                    
                if history:
                    patterns.append({
                        'entity_id': entity.id,
                        'history': sorted(history, key=lambda x: x['timestamp'])
                    })
                    
        return patterns

    def find_causal_patterns(self,
                            entity_id: UUID,
                            min_confidence: float = 0.5,
                            max_depth: int = 5) -> List[Dict[str, Any]]:
        """Identify causal patterns starting from an entity."""
        chains = self.store.get_causal_chain(
            entity_id=entity_id,
            max_depth=max_depth,
            min_confidence=min_confidence
        )
        
        patterns = []
        for chain in chains:
            pattern = {
                'entities': [],
                'relationships': []
            }
            
            for i, entity_id in enumerate(chain):
                entity = self.store.get_entity(entity_id)
                if entity:
                    pattern['entities'].append({
                        'id': entity.id,
                        'type': entity.type,
                        'properties': {k: v.value for k, v in entity.properties.items()}
                    })
                    
                    if i < len(chain) - 1:
                        relationships = self.store.get_relationships(entity_id)
                        for rel in relationships:
                            if rel.target_id == chain[i + 1]:
                                pattern['relationships'].append({
                                    'type': rel.type,
                                    'causal_strength': rel.causal_strength,
                                    'properties': {k: v.value for k, v in rel.properties.items()}
                                })
                                break
                                
            patterns.append(pattern)
            
        return patterns