from datetime import datetime, UTC
from typing import Dict, Any, List

class ContextualPatternDetector:
    def learn_from_source(self, source_type: str, content: Dict[str, Any], confidence: float) -> None:
        """Learn patterns from a source."""
        # Process relationships
        if "relationships" in content:
            for rel in content["relationships"]:
                self._process_relationship(rel, source_type, confidence)
        
        # Save checkpoint
        self._save_checkpoint()

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