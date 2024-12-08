from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
import copy

from .power_structure import PowerStructure
from ..memory.vector_store import VectorStoreMemory
from ..memory.timeline import Timeline
from ..persistence.checkpointer import Checkpointer
from ..state_management.api_state import APIState

class ContextualPatternDetector:
    def __init__(self):
        """Initialize detector with dependencies."""
        self.power_structure = PowerStructure()
        self.vector_memory = VectorStoreMemory()
        self.timeline = Timeline()
        self.state = APIState()
        self.checkpointer = None  # Will be injected by test fixture

    def learn_from_source(self, source_type: str, content: Dict[str, Any], confidence: float) -> None:
        """Learn patterns from a source."""
        # Store initial state
        initial_state = copy.deepcopy(self.state.to_dict())
        
        # Process relationships
        if "relationships" in content:
            for rel in content["relationships"]:
                self._process_relationship(rel, source_type, confidence)

        # Process entities
        if "entities" in content:
            for entity in content["entities"]:
                self._process_entity(entity, source_type, confidence)
        
        # Update state
        self.state.request_history.append({
            "type": "learn_from_source",
            "source_type": source_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": {
                "entities": len(content.get("entities", [])),
                "relationships": len(content.get("relationships", [])),
                "confidence": confidence,
                "initial_state": initial_state
            }
        })
        
        # Save checkpoint
        self._save_checkpoint()

    def _process_entity(self, entity: Dict[str, Any], source_type: str, confidence: float) -> None:
        """Process an entity update."""
        entity_id = entity.get("id")
        entity_type = entity.get("type")
        entity_name = entity.get("name")
        properties = entity.get("properties", {})

        if entity_id and entity_type:
            # Add to power structure with confidence
            self.power_structure.add_entity(entity_id, entity_type, properties, confidence)

            # Create memory text combining name and properties
            memory_text = f"{entity_name or entity_id}: {properties}"
            
            # Add to vector memory
            self.vector_memory.add_memory(
                text=memory_text,
                metadata={
                    "entity_id": entity_id,
                    "type": entity_type,
                    "source_type": source_type,
                    "confidence": confidence
                }
            )

            # Add to timeline
            self.timeline.add_event({
                "type": "entity_created",
                "entity_id": entity_id,
                "entity_type": entity_type,
                "timestamp": datetime.now(UTC)
            })

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
        if self.checkpointer:
            self.checkpointer.save(checkpoint_data)
    
    def load_checkpoint(self) -> None:
        """Load state from checkpoint."""
        if self.checkpointer:
            checkpoint_data = self.checkpointer.load()
            if checkpoint_data:
                # TODO: Implement state restoration
                pass
    
    def search_patterns(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for patterns using semantic similarity."""
        return self.vector_memory.get_relevant_memories(query, k)