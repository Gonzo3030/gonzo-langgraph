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
        
    def to_checkpoint(self) -> Dict[str, Any]:
        """Convert to checkpoint format."""
        return {
            "entities": {id: vars(entity) for id, entity in self.entities.items()},
            "influence_networks": self.influence_networks,
            "financial_relationships": self.financial_relationships,
            "policy_alignments": self.policy_alignments
        }