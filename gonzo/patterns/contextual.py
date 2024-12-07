
    def _process_relationship(
        self,
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