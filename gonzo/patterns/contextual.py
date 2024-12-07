
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
    
    def add_entity(self, 
        id: str,
        name: str,
        entity_type: str,
        properties: Dict[str, Any] = None
    ) -> Optional[Entity]:
        """Add a new entity to the power structure."""
        if entity_type not in self.entity_types:
            logger.error(f"Invalid entity type: {entity_type}")
            return None
            
        # Convert regular properties to KnowledgeClaims if needed
        property_claims = {}
        if properties:
            for key, value in properties.items():
                if isinstance(value, KnowledgeClaim):
                    property_claims[key] = value
                else:
                    property_claims[key] = KnowledgeClaim(
                        value=value,
                        source="initial_data",
                        confidence=ConfidenceLevel.MEDIUM
                    )
        
        entity = Entity(id, name, entity_type, property_claims)
        self.entities[id] = entity
        return entity
    
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
        
    def to_checkpoint(self) -> Dict[str, Any]:
        """Convert to checkpoint format."""
        return {
            "entities": {id: vars(entity) for id, entity in self.entities.items()},
            "influence_networks": self.influence_networks,
            "financial_relationships": self.financial_relationships,
            "policy_alignments": self.policy_alignments
        }