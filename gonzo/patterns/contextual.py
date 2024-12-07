class ContextualPatternDetector:
    """Detects manipulation patterns using contextual awareness."""
    
    def __init__(self, state: Optional[APIState] = None):
        self.power_structure = PowerStructure()
        self.vector_memory = VectorStoreMemory()
        self.timeline = Timeline()
        self.checkpointer = Checkpointer()
        self.store = Store()
        self.state = state or APIState()

    def learn_from_source(self,
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
        
        # Process relationships
        if "relationships" in content:
            for rel in content["relationships"]:
                self._process_relationship(rel, source_type, confidence)
        
        # Save checkpoint
        self._save_checkpoint()
    
    def _process_relationship(self,
        rel: Dict[str, Any],
        source_type: str,
        confidence: float
    ) -> None:
        """Process a relationship update."""
        source_id = rel.get("source")
        target_id = rel.get("target")
        rel_type = rel.get("type")
        
        if all([source_id, target_id, rel_type]):
            # Learn basic relationship
            self.power_structure.learn_relationship(
                source_id,
                target_id,
                rel_type,
                confidence,
                source_type
            )
            
            # Add to timeline
            self.timeline.add_event({
                "type": "relationship_created",
                "source": source_id,
                "target": target_id,
                "relationship_type": rel_type,
                "timestamp": datetime.now(UTC)
            })
            
            # Process specific relationship types
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
    
    def _save_checkpoint(self) -> None:
        """Save current state to checkpoint."""
        checkpoint_data = {
            "power_structure": self.power_structure.to_checkpoint(),
            "timeline": self.timeline.to_checkpoint(),
            "state": self.state.to_dict()
        }
        self.checkpointer.save(checkpoint_data)
    
    def load_checkpoint(self) -> None:
        """Load state from checkpoint."""
        checkpoint_data = self.checkpointer.load()
        if checkpoint_data:
            # TODO: Implement state restoration
            pass
    
    def search_patterns(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for patterns using semantic similarity."""
        return self.vector_memory.get_relevant_memories(query, k)