
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