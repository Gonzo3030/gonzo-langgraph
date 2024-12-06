from typing import Dict, Any, List
from datetime import datetime
import logging
from uuid import uuid4
from langsmith import traceable

from ..graph.knowledge.graph import KnowledgeGraph
from ..graph.knowledge.types import Entity, Relationship
from ..graph.state import GonzoState

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KnowledgeEnhancedNarrative:
    """Enhances narrative analysis with knowledge graph integration."""
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        
    def _extract_narrative_entities(self, analysis: Dict[str, Any]) -> List[Entity]:
        """Extract entities from narrative analysis."""
        entities = []
        
        # Create a narrative event entity
        narrative_entity = self.knowledge_graph.add_entity(
            entity_type="narrative_event",
            properties={
                "content": analysis.get("raw_analysis", ""),
                "timestamp": analysis.get("timestamp", datetime.now().isoformat()),
                "thread_format": analysis.get("tweet_thread", [])
            },
            temporal=True,
            valid_from=datetime.fromisoformat(analysis.get("timestamp", datetime.now().isoformat()))
        )
        entities.append(narrative_entity)
        
        return entities
        
    def _create_narrative_relationships(self, 
                                       new_entity: Entity,
                                       state: GonzoState) -> List[Relationship]:
        """Create relationships between narrative entities."""
        relationships = []
        
        # Get previous narrative analyses from memory
        prev_analyses = state.get_from_memory("narrative_analyses", "long_term") or []
        
        for prev_analysis in prev_analyses:
            if "entity_id" in prev_analysis:
                prev_entity = self.knowledge_graph.get_entity(prev_analysis["entity_id"])
                if prev_entity:
                    # Create temporal relationship
                    relationship = self.knowledge_graph.add_relationship(
                        relationship_type="narrative_sequence",
                        source_id=prev_entity.id,
                        target_id=new_entity.id,
                        temporal_ordering="before"
                    )
                    relationships.append(relationship)
        
        return relationships

@traceable(name="enhance_narrative_knowledge")
async def enhance_narrative(state: GonzoState) -> Dict[str, Any]:
    """Enhance narrative analysis with knowledge graph integration."""
    try:
        enhancer = KnowledgeEnhancedNarrative()
        
        # Get the latest narrative analysis
        latest_analysis = state.get_from_memory("last_narrative_analysis", "long_term")
        if not latest_analysis:
            logger.error("No narrative analysis found in memory")
            return {"next": state.get_next_step()}
        
        # Extract entities and create relationships
        entities = enhancer._extract_narrative_entities(latest_analysis)
        if entities:
            main_entity = entities[0]
            relationships = enhancer._create_narrative_relationships(main_entity, state)
            
            # Update memory with entity reference
            analysis_record = {
                **latest_analysis,
                "entity_id": main_entity.id,
                "related_entities": [e.id for e in entities[1:]],
                "relationships": [r.id for r in relationships]
            }
            
            # Get existing analyses or initialize new list
            narrative_analyses = state.get_from_memory("narrative_analyses", "long_term") or []
            narrative_analyses.append(analysis_record)
            
            # Save back to memory
            state.save_to_memory(
                key="narrative_analyses",
                value=narrative_analyses,
                permanent=True
            )
            
            logger.debug(f"Enhanced narrative analysis with knowledge graph integration: {analysis_record}")
            
        return {"next": state.get_next_step()}
        
    except Exception as e:
        error_msg = f"Knowledge enhancement error: {str(e)}"
        logger.error(error_msg)
        state.add_error(error_msg)
        return {"next": "error"}
