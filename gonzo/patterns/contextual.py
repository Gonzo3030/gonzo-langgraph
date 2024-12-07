"""Contextual pattern detection with dynamic knowledge updating."""

from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, UTC
from uuid import UUID
import logging
from enum import Enum

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
    
    def learn_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        confidence: float,
        info_source: str
    ) -> bool:
        """Learn or update a relationship between entities."""
        if source_id not in self.entities or target_id not in self.entities:
            return False
            
        source_entity = self.entities[source_id]
        
        if relationship_type not in source_entity.relationships:
            logger.warning(f"Unknown relationship type: {relationship_type}")
            return False
            
        relationships = source_entity.relationships[relationship_type]
        
        if target_id in relationships:
            # Update existing relationship
            existing = relationships[target_id]
            if confidence > existing.confidence:
                relationships[target_id] = KnowledgeClaim(
                    value=True,
                    source=info_source,
                    confidence=confidence
                )
            else:
                existing.add_corroboration(info_source, confidence)
        else:
            # New relationship
            relationships[target_id] = KnowledgeClaim(
                value=True,
                source=info_source,
                confidence=confidence
            )
        
        return True
    
    def learn_influence_relationship(
        self,
        source_id: str,
        target_id: str,
        influence_strength: float,
        evidence: str,
        confidence: float
    ) -> None:
        """Learn about influence relationships between entities."""
        if source_id not in self.influence_networks:
            self.influence_networks[source_id] = {}
        
        # Weight the influence by confidence
        adjusted_influence = influence_strength * confidence
        self.influence_networks[source_id][target_id] = adjusted_influence
        
        # Record the evidence
        self.learn_relationship(
            source_id,
            target_id,
            "influences",
            confidence,
            evidence
        )
    
    def learn_financial_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_details: Dict[str, Any],
        source: str,
        confidence: float
    ) -> None:
        """Learn about financial relationships between entities."""
        if source_id not in self.financial_relationships:
            self.financial_relationships[source_id] = {}
            
        self.financial_relationships[source_id][target_id] = KnowledgeClaim(
            value=relationship_details,
            source=source,
            confidence=confidence
        )
    
    def learn_policy_alignment(
        self,
        entity1_id: str,
        entity2_id: str,
        alignment_score: float,
        topics: List[str]
    ) -> None:
        """Learn about policy alignment between entities."""
        if entity1_id not in self.policy_alignments:
            self.policy_alignments[entity1_id] = {}
            
        self.policy_alignments[entity1_id][entity2_id] = alignment_score
        
        # Also store the reverse relationship
        if entity2_id not in self.policy_alignments:
            self.policy_alignments[entity2_id] = {}
        self.policy_alignments[entity2_id][entity1_id] = alignment_score

class ContextualPatternDetector:
    """Detects manipulation patterns using contextual awareness."""
    
    def __init__(self):
        self.power_structure = PowerStructure()
        
    def learn_from_source(self,
        source_type: str,
        content: Dict[str, Any],
        confidence: float
    ) -> None:
        """Learn new information from a data source.
        
        Args:
            source_type: Type of source (e.g., 'news', 'financial_report', 'social_media')
            content: Dictionary containing the information
            confidence: Confidence level in the source
        """
        # Extract entities
        if "entities" in content:
            for entity_data in content["entities"]:
                entity_id = entity_data.get("id")
                if entity_id:
                    if entity_id not in self.power_structure.entities:
                        # New entity
                        self.power_structure.add_entity(
                            id=entity_id,
                            name=entity_data.get("name", entity_id),
                            entity_type=entity_data.get("type", "unknown"),
                            properties=entity_data.get("properties", {})
                        )
                    else:
                        # Update existing entity
                        entity = self.power_structure.entities[entity_id]
                        for key, value in entity_data.get("properties", {}).items():
                            entity.update_property(key, value, source_type, confidence)
        
        # Extract relationships
        if "relationships" in content:
            for rel in content["relationships"]:
                source_id = rel.get("source")
                target_id = rel.get("target")
                rel_type = rel.get("type")
                
                if all([source_id, target_id, rel_type]):
                    self.power_structure.learn_relationship(
                        source_id,
                        target_id,
                        rel_type,
                        confidence,
                        source_type
                    )
                    
                    # Check for specific relationship types
                    if "influence" in rel:
                        self.power_structure.learn_influence_relationship(
                            source_id,
                            target_id,
                            rel["influence"].get("strength", 0.5),
                            source_type,
                            confidence
                        )
                    
                    if "financial" in rel:
                        self.power_structure.learn_financial_relationship(
                            source_id,
                            target_id,
                            rel["financial"],
                            source_type,
                            confidence
                        )
                    
                    if "policy_alignment" in rel:
                        self.power_structure.learn_policy_alignment(
                            source_id,
                            target_id,
                            rel["policy_alignment"].get("score", 0.5),
                            rel["policy_alignment"].get("topics", [])
                        )