from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from langsmith import traceable

from ..graph.knowledge.graph import KnowledgeGraph
from ..graph.knowledge.types import Entity, Relationship, Property
from ..graph.state import GonzoState
from .new_assessment import assess_input

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KnowledgeEnhancedAssessment:
    """Enhances assessment with knowledge graph capabilities."""
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        
    def _create_topic_entity(self, assessment: Dict[str, Any]) -> Entity:
        """Create an entity representing the assessed topic."""
        return self.knowledge_graph.add_entity(
            entity_type="topic",
            properties={
                "category": assessment["category"],
                "raw_category": assessment["raw_category"],
                "content": assessment["message_content"],
                "timestamp": assessment["timestamp"]
            },
            temporal=True,
            valid_from=datetime.fromisoformat(assessment["timestamp"])
        )
        
    def _create_topic_relationships(self,
                                   current_topic: Entity,
                                   state: GonzoState) -> List[Relationship]:
        """Create relationships between topics."""
        relationships = []
        
        # Get previous assessments
        prev_assessments = state.get_from_memory("topic_assessments", "long_term") or []
        
        if prev_assessments:
            # Get the most recent previous assessment
            prev_assessment = prev_assessments[-1]
            if "entity_id" in prev_assessment:
                prev_topic = self.knowledge_graph.get_entity(prev_assessment["entity_id"])
                if prev_topic:
                    # Create topic transition relationship
                    relationship = self.knowledge_graph.add_relationship(
                        relationship_type="topic_transition",
                        source_id=prev_topic.id,
                        target_id=current_topic.id,
                        properties={
                            "from_category": prev_topic.properties["category"].value,
                            "to_category": current_topic.properties["category"].value
                        },
                        temporal_ordering="before"
                    )
                    relationships.append(relationship)
                    
                    # If topics are related, create additional relationship
                    if self._are_topics_related(prev_topic, current_topic):
                        related_rel = self.knowledge_graph.add_relationship(
                            relationship_type="topic_relation",
                            source_id=prev_topic.id,
                            target_id=current_topic.id,
                            properties={
                                "relation_type": self._get_relation_type(
                                    prev_topic.properties["category"].value,
                                    current_topic.properties["category"].value
                                )
                            }
                        )
                        relationships.append(related_rel)
                        
        return relationships
    
    def _are_topics_related(self, topic1: Entity, topic2: Entity) -> bool:
        """Determine if two topics are related based on their categories and content."""
        # Check for direct category relationships
        related_pairs = {
            frozenset(["crypto", "narrative"]),  # Crypto and narrative manipulation often related
            frozenset(["narrative", "general"])  # General topics might evolve into narratives
        }
        
        current_pair = frozenset([
            topic1.properties["category"].value,
            topic2.properties["category"].value
        ])
        
        return current_pair in related_pairs
    
    def _get_relation_type(self, category1: str, category2: str) -> str:
        """Determine the type of relationship between categories."""
        if {category1, category2} == {"crypto", "narrative"}:
            return "narrative_influence"
        elif {category1, category2} == {"narrative", "general"}:
            return "narrative_evolution"
        return "temporal_sequence"

@traceable(name="enhance_assessment")
async def enhance_assessment(state: GonzoState) -> Dict[str, Any]:
    """Enhance assessment with knowledge graph integration."""
    try:
        # First, run the regular assessment
        assessment_result = await assess_input(state)
        if assessment_result["next"] == "error":
            return assessment_result
            
        # Get the assessment data from memory
        latest_assessment = state.get_from_memory("last_assessment")
        if not latest_assessment:
            logger.error("No assessment found in memory")
            return assessment_result
            
        # Enhance with knowledge graph
        enhancer = KnowledgeEnhancedAssessment()
        
        # Create topic entity
        topic_entity = enhancer._create_topic_entity(latest_assessment)
        
        # Create relationships with previous topics
        relationships = enhancer._create_topic_relationships(topic_entity, state)
        
        # Update memory with entity reference
        assessment_record = {
            **latest_assessment,
            "entity_id": topic_entity.id,
            "relationships": [r.id for r in relationships]
        }
        
        # Get existing assessments or initialize new list
        topic_assessments = state.get_from_memory("topic_assessments", "long_term") or []
        topic_assessments.append(assessment_record)
        
        # Save back to memory
        state.save_to_memory(
            key="topic_assessments",
            value=topic_assessments,
            permanent=True
        )
        
        logger.debug(f"Enhanced assessment with knowledge graph integration: {assessment_record}")
        
        return assessment_result
        
    except Exception as e:
        error_msg = f"Knowledge enhancement error: {str(e)}"
        logger.error(error_msg)
        state.add_error(error_msg)
        state.set_next_step("error")
        return {"next": "error"}