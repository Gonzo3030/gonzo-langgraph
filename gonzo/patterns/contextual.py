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