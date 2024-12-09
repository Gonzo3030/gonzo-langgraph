from typing import Dict, List, Optional
from datetime import datetime, timedelta, UTC
import logging

from .emotional import EmotionalManipulationDetector
from ..types import TimeAwareEntity, Property
from ..graph.knowledge import KnowledgeGraph

logger = logging.getLogger(__name__)

class ManipulationDetector:
    def __init__(self, graph: KnowledgeGraph, min_confidence: float = 0.6):
        self.graph = graph
        self.min_confidence = min_confidence
        self.emotional_detector = EmotionalManipulationDetector(
            min_confidence=min_confidence
        )

    def detect_narrative_manipulation(self, timeframe: int = 3600) -> List[Dict]:
        # Get all topics in timeframe
        all_topics = self.graph.get_entities_by_type("topic")
        topics = []
        
        now = datetime.now(UTC)
        start_time = now - timedelta(seconds=timeframe)
        
        for topic in all_topics:
            if not isinstance(topic, TimeAwareEntity):
                continue
            if not topic.valid_from:
                continue
            if topic.valid_from.tzinfo is None:
                topic.valid_from = topic.valid_from.replace(tzinfo=UTC)
            if topic.valid_from >= start_time:
                topics.append(topic)
        
        if not topics:
            return []
            
        patterns = []
        
        # Check for emotional manipulation
        emotional = self.emotional_detector.detect_emotional_escalation(topics)
        if emotional:
            patterns.append(emotional)
        
        # Check for narrative repetition
        for topic in topics:
            if "category" not in topic.properties or "keywords" not in topic.properties:
                continue
                
            topic_category = topic.properties["category"].value
            topic_keywords = set(topic.properties["keywords"].value)
            
            similar_topics = []
            for other in topics:
                if other.id == topic.id:
                    continue
                if "category" not in other.properties or "keywords" not in other.properties:
                    continue
                if other.properties["category"].value != topic_category:
                    continue
                    
                other_keywords = set(other.properties["keywords"].value)
                if topic_keywords == other_keywords:
                    similar_topics.append(other)
            
            if len(similar_topics) >= 2:
                patterns.append({
                    "pattern_type": "narrative_repetition",
                    "category": topic_category,
                    "topic_count": len(similar_topics) + 1,
                    "confidence": 1.0,
                    "metadata": {
                        "base_topic_id": str(topic.id),
                        "related_topic_ids": [str(t.id) for t in similar_topics]
                    }
                })
        
        # Check for coordinated shifts
        for topic in topics:
            transitions = self.graph.get_relationships_by_type(
                relationship_type="topic_transition",
                source_id=topic.id
            )
            
            if len(transitions) < 2:
                continue
            
            by_target = {}
            for trans in transitions:
                target = str(trans.target_id)
                if target not in by_target:
                    by_target[target] = set()
                    
                if "source_entity_id" in trans.properties:
                    source = str(trans.properties["source_entity_id"])
                    by_target[target].add(source)
            
            for target, sources in by_target.items():
                if len(sources) >= 2:
                    patterns.append({
                        "pattern_type": "coordinated_shift",
                        "topic_id": str(topic.id),
                        "confidence": len(sources) / len(transitions),
                        "metadata": {
                            "target_id": target,
                            "source_count": len(sources),
                            "source_ids": list(sources)
                        }
                    })
        
        return patterns