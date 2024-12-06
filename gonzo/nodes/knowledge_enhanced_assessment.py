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
    
    _instance = None
    _graph = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._graph = KnowledgeGraph()
        return cls._instance
    
    def _create_topic_entity(self, assessment: Dict[str, Any]) -> Entity:
        """Create an entity representing the assessed topic."""
        logger.debug(f"Creating topic entity for assessment: {assessment}")
        return self._graph.add_entity(
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
        logger.debug("Creating topic relationships")
        
        # Get previous assessments from long-term memory
        prev_assessments = state.get_from_memory("topic_assessments", "long_term")
        logger.debug(f"Found previous assessments: {prev_assessments}")
        
        if prev_assessments:
            # Get the most recent previous assessment
            prev_assessment = prev_assessments[-1]
            if "entity_id" in prev_assessment:
                prev_topic = self._graph.get_entity(prev_assessment["entity_id"])
                logger.debug(f"Found previous topic: {prev_topic}")
                
                if prev_topic:
                    # Create topic transition relationship
                    transition_rel = self._graph.add_relationship(
                        relationship_type="topic_transition",
                        source_id=prev_topic.id,
                        target_id=current_topic.id,
                        properties={
                            "from_category": prev_topic.properties["category"].value,
                            "to_category": current_topic.properties["category"].value,
                            "transition_time": (datetime.fromisoformat(current_topic.properties["timestamp"].value) - 
                                              datetime.fromisoformat(prev_topic.properties["timestamp"].value)).total_seconds()
                        }
                    )
                    relationships.append(transition_rel)
                    logger.debug(f"Created transition relationship: {transition_rel}")
                    
                    # Check for topic relations
                    if self._are_topics_related(prev_topic, current_topic):
                        relation_type = self._get_relation_type(
                            prev_topic.properties["category"].value,
                            current_topic.properties["category"].value
                        )
                        logger.debug(f"Topics are related with type: {relation_type}")
                        
                        related_rel = self._graph.add_relationship(
                            relationship_type="topic_relation",
                            source_id=prev_topic.id,
                            target_id=current_topic.id,
                            properties={
                                "relation_type": relation_type,
                                "strength": self._calculate_relation_strength(
                                    prev_topic, current_topic, relation_type
                                )
                            }
                        )
                        relationships.append(related_rel)
                        logger.debug(f"Created relation relationship: {related_rel}")
        
        return relationships
    
    def _are_topics_related(self, topic1: Entity, topic2: Entity) -> bool:
        """Determine if two topics are related based on their categories and content."""
        # Get category values
        cat1 = topic1.properties["category"].value
        cat2 = topic2.properties["category"].value
        
        # Define related category pairs
        related_pairs = {
            frozenset(["crypto", "narrative"]),  # Crypto and narrative manipulation often related
            frozenset(["narrative", "general"]),  # General topics might evolve into narratives
            frozenset(["crypto", "general"])  # General topics might relate to crypto
        }
        
        current_pair = frozenset([cat1, cat2])
        logger.debug(f"Checking relation between categories: {current_pair}")
        return current_pair in related_pairs
    
    def _get_relation_type(self, category1: str, category2: str) -> str:
        """Determine the type of relationship between categories."""
        pair = frozenset([category1, category2])
        
        if pair == frozenset(["crypto", "narrative"]):
            return "narrative_influence"
        elif pair == frozenset(["narrative", "general"]):
            return "narrative_evolution"
        elif pair == frozenset(["crypto", "general"]):
            return "market_impact"
        return "temporal_sequence"
    
    def _calculate_relation_strength(self, topic1: Entity, topic2: Entity, relation_type: str) -> float:
        """Calculate the strength of relationship between topics."""
        # Start with a base strength
        strength = 0.5
        
        # Adjust based on time proximity (closer in time = stronger relationship)
        time1 = datetime.fromisoformat(topic1.properties["timestamp"].value)
        time2 = datetime.fromisoformat(topic2.properties["timestamp"].value)
        time_diff = abs((time2 - time1).total_seconds() / 3600)  # Convert to hours
        
        # Decay strength based on time difference (max 24 hours)
        time_factor = max(0, 1 - (time_diff / 24))
        strength += time_factor * 0.3
        
        # Boost strength for certain relation types
        if relation_type == "narrative_influence":
            strength += 0.2
        elif relation_type == "narrative_evolution":
            strength += 0.1
        
        return min(1.0, strength)

@traceable(name="enhance_assessment")
async def enhance_assessment(state: GonzoState) -> Dict[str, Any]:
    """Enhance assessment with knowledge graph integration."""
    try:
        logger.debug("Starting enhanced assessment")
        
        # First, run the regular assessment
        assessment_result = await assess_input(state)
        if assessment_result["next"] == "error":
            return assessment_result
            
        # Get the assessment data from memory
        latest_assessment = state.get_from_memory("last_assessment")
        if not latest_assessment:
            logger.error("No assessment found in memory")
            return assessment_result
            
        logger.debug(f"Got latest assessment: {latest_assessment}")
        
        # Enhance with knowledge graph
        enhancer = KnowledgeEnhancedAssessment()
        
        # Create topic entity
        topic_entity = enhancer._create_topic_entity(latest_assessment)
        logger.debug(f"Created topic entity: {topic_entity}")
        
        # Create relationships with previous topics
        relationships = enhancer._create_topic_relationships(topic_entity, state)
        logger.debug(f"Created relationships: {relationships}")
        
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