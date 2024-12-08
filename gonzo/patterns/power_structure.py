from typing import Dict, Any, Optional, List
from datetime import datetime, UTC

class Entity:
    def __init__(self, id: str, type: str, properties: Dict[str, Any] = None, confidence: float = 1.0):
        self.id = id
        self.type = type
        self.properties = {}
        if properties:
            for k, v in properties.items():
                self.properties[k] = Property(v, confidence)

class Property:
    def __init__(self, value: Any, confidence: float = 1.0):
        self.value = value
        self.confidence = confidence

class PowerStructure:
    """Tracks relationships and influence between entities."""

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Dict[str, List[str]]] = {}
        self.influence_networks: Dict[str, Dict[str, float]] = {}
        self.financial_relationships: Dict[str, Dict[str, Property]] = {}
        self.policy_alignments: Dict[str, Dict[str, float]] = {}

    def learn_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        confidence: float,
        source_type: str
    ) -> None:
        """Learn a basic relationship between entities."""
        if source_id not in self.relationships:
            self.relationships[source_id] = {}
        if target_id not in self.relationships[source_id]:
            self.relationships[source_id][target_id] = []
        self.relationships[source_id][target_id].append(rel_type)

    def learn_influence_relationship(
        self,
        source_id: str,
        target_id: str,
        strength: float,
        source_type: str,
        confidence: float
    ) -> None:
        """Learn influence relationship strength."""
        if source_id not in self.influence_networks:
            self.influence_networks[source_id] = {}
        self.influence_networks[source_id][target_id] = strength * confidence

    def learn_financial_relationship(
        self,
        source_id: str,
        target_id: str,
        data: Dict[str, Any],
        source_type: str,
        confidence: float
    ) -> None:
        """Learn financial relationship details."""
        if source_id not in self.financial_relationships:
            self.financial_relationships[source_id] = {}
        self.financial_relationships[source_id][target_id] = Property(data, confidence)

    def learn_policy_alignment(
        self,
        entity1_id: str,
        entity2_id: str,
        score: float,
        topics: List[str]
    ) -> None:
        """Learn policy alignment between entities."""
        if entity1_id not in self.policy_alignments:
            self.policy_alignments[entity1_id] = {}
        self.policy_alignments[entity1_id][entity2_id] = score

    def add_entity(self, entity_id: str, type: str, properties: Dict[str, Any] = None, confidence: float = 1.0) -> None:
        """Add a new entity to the structure."""
        if entity_id not in self.entities:
            self.entities[entity_id] = Entity(entity_id, type, properties, confidence)

    def to_checkpoint(self) -> Dict[str, Any]:
        """Convert state to checkpoint format."""
        return {
            "entities": {
                id: {
                    "type": e.type,
                    "properties": {
                        k: {"value": v.value, "confidence": v.confidence}
                        for k, v in e.properties.items()
                    }
                }
                for id, e in self.entities.items()
            },
            "relationships": self.relationships,
            "influence_networks": self.influence_networks,
            "financial_relationships": {
                s: {
                    t: {"value": p.value, "confidence": p.confidence}
                    for t, p in rels.items()
                }
                for s, rels in self.financial_relationships.items()
            },
            "policy_alignments": self.policy_alignments
        }