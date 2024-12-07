
class ContextualPatternDetector:
    """Detects manipulation patterns using contextual awareness."""
    
    def __init__(self, state: Optional[APIState] = None):
        self.power_structure = PowerStructure()
        self.vector_memory = VectorStoreMemory()
        self.timeline = Timeline()
        self.checkpointer = Checkpointer()
        self.store = Store()
        self.state = state or APIState()

    def learn_from_source(
        self,
        source_type: str,
        content: Dict[str, Any],
        confidence: float
    ) -> None:
        """Learn new information from a data source."""
        # Extract entities and store in vector memory
        if "entities" in content:
            for entity_data in content["entities"]:
                entity_id = entity_data.get("id")
                if entity_id:
                    # Create or update entity
                    properties = {}
                    for key, value in entity_data.get("properties", {}).items():
                        claim = KnowledgeClaim(
                            value=value,
                            source=source_type,
                            confidence=confidence
                        )
                        properties[key] = claim
                        
                        # Store in vector memory for semantic search
                        self.vector_memory.add_memory(
                            **claim.to_memory_entry()
                        )
                    
                    if entity_id not in self.power_structure.entities:
                        # New entity
                        entity = self.power_structure.add_entity(
                            id=entity_id,
                            name=entity_data.get("name", entity_id),
                            entity_type=entity_data.get("type", "unknown"),
                            properties=properties
                        )
                        
                        # Add to timeline
                        self.timeline.add_event({
                            "type": "entity_created",
                            "entity_id": entity_id,
                            "timestamp": datetime.now(UTC)
                        })
                    else:
                        # Update existing entity
                        entity = self.power_structure.entities[entity_id]
                        for key, value in properties.items():
                            entity.update_property(
                                key=key,
                                value=value.value,
                                source=source_type,
                                confidence=confidence
                            )
                            
                            # Add update to timeline
                            self.timeline.add_event({
                                "type": "entity_updated",
                                "entity_id": entity_id,
                                "property": key,
                                "timestamp": datetime.now(UTC)
                            })