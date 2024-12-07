
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