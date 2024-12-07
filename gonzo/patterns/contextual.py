
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