"""Contextual pattern detection with dynamic knowledge updating."""

[Previous content remains the same until ContextualPatternDetector class]

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
                    # Convert properties to KnowledgeClaims with provided confidence
                    properties = {}
                    for key, value in entity_data.get("properties", {}).items():
                        properties[key] = KnowledgeClaim(
                            value=value,
                            source=source_type,
                            confidence=confidence
                        )
                    
                    if entity_id not in self.power_structure.entities:
                        # New entity
                        self.power_structure.add_entity(
                            id=entity_id,
                            name=entity_data.get("name", entity_id),
                            entity_type=entity_data.get("type", "unknown"),
                            properties=properties  # Pass pre-created KnowledgeClaims
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