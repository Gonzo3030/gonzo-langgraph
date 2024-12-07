
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