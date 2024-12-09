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
        logger.debug(f"Found {len(all_topics)} total topics")
        
        # Filter for timeframe
        now = datetime.now(UTC)
        start_time = now - timedelta(seconds=timeframe)
        logger.debug(f"Filtering for topics after {start_time} (UTC)")
        
        valid_topics = []
        for t in all_topics:
            if not isinstance(t, TimeAwareEntity) or not t.valid_from:
                logger.debug(f"Topic {t.id} is not time-aware or missing valid_from")
                continue
                
            # Ensure topic time is UTC
            topic_time = t.valid_from if t.valid_from.tzinfo else t.valid_from.replace(tzinfo=UTC)
            
            logger.debug(f"Checking topic {t.id} with time {topic_time}")
            logger.debug(f"Comparing {topic_time} >= {start_time}")
            
            if topic_time >= start_time:
                logger.debug(f"Topic {t.id} is within timeframe")
                valid_topics.append(t)
        
        logger.debug(f"Found {len(valid_topics)} topics in timeframe")
        if not valid_topics:
            return []

        # Log full details of topics for inspection
        for topic in valid_topics:
            logger.debug(f"Valid topic: {topic.id}")
            logger.debug(f"  valid_from: {topic.valid_from}")
            logger.debug(f"  valid_to: {topic.valid_to}")
            logger.debug(f"  properties: {topic.properties}")
        
        # Detect patterns
        patterns = []
        
        # 1. Emotional manipulation check
        emotional = self.emotional_detector.detect_emotional_escalation(valid_topics)
        if emotional:
            patterns.append(emotional)
            logger.debug("Found emotional manipulation pattern")
        
        # 2. Narrative repetition check
        narratives = self._find_narrative_patterns(valid_topics)
        if narratives:
            patterns.extend(narratives)
            logger.debug(f"Found {len(narratives)} narrative patterns")
        
        # 3. Coordinated shift check
        shifts = self._find_coordinated_shifts(valid_topics)
        if shifts:
            patterns.extend(shifts)
            logger.debug(f"Found {len(shifts)} coordinated shift patterns")
        
        logger.debug(f"Total patterns found: {len(patterns)}")
        return patterns
        
    def _find_narrative_patterns(self, topics: List[TimeAwareEntity]) -> List[Dict]:
        logger.debug(f"Checking for narrative patterns in {len(topics)} topics")
        patterns = []
        for topic in topics:
            if "category" not in topic.properties or "keywords" not in topic.properties:
                logger.debug(f"Topic {topic.id} missing category or keywords")
                continue
                
            topic_category = topic.properties["category"].value
            topic_keywords = set(topic.properties["keywords"].value)
            
            logger.debug(f"Checking topic {topic.id} in category {topic_category}")
            logger.debug(f"Keywords: {topic_keywords}")
            
            similar_topics = [
                other for other in topics
                if other.id != topic.id
                and "category" in other.properties
                and other.properties["category"].value == topic_category
                and "keywords" in other.properties
                and set(other.properties["keywords"].value) == topic_keywords
            ]
            
            if len(similar_topics) >= 2:
                pattern = {
                    "pattern_type": "narrative_repetition",
                    "category": topic_category,
                    "topic_count": len(similar_topics) + 1,
                    "confidence": 1.0,
                    "metadata": {
                        "base_topic_id": str(topic.id),
                        "related_topic_ids": [str(t.id) for t in similar_topics]
                    }
                }
                patterns.append(pattern)
                logger.debug(f"Found narrative pattern: {pattern}")
                
        return patterns

    def _find_coordinated_shifts(self, topics: List[TimeAwareEntity]) -> List[Dict]:
        patterns = []
        for topic in topics:
            transitions = self.graph.get_relationships_by_type(
                relationship_type="topic_transition",
                source_id=topic.id
            )
            
            if len(transitions) < 2:
                continue
            
            # Group by target
            by_target = {}
            for trans in transitions:
                target = str(trans.target_id)
                if target not in by_target:
                    by_target[target] = set()
                    
                if "source_entity_id" in trans.properties:
                    source = str(trans.properties["source_entity_id"])
                    by_target[target].add(source)
            
            # Look for multiple sources to same target
            for target, sources in by_target.items():
                if len(sources) >= 2:
                    pattern = {
                        "pattern_type": "coordinated_shift",
                        "topic_id": str(topic.id),
                        "confidence": len(sources) / len(transitions),
                        "metadata": {
                            "target_id": target,
                            "source_count": len(sources),
                            "source_ids": list(sources)
                        }
                    }
                    patterns.append(pattern)
                    logger.debug(f"Found coordinated shift: {pattern}")
                    break
        
        return patterns