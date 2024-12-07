
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