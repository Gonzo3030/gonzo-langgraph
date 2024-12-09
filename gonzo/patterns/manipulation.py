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
        # Get all topics
        all_topics = self.graph.get_entities_by_type("topic")
        
        # Filter within timeframe
        now = datetime.now(UTC)
        start_time = now - timedelta(seconds=timeframe)
        
        valid_topics = []
        for topic in all_topics:
            if not isinstance(topic, TimeAwareEntity):
                continue
            if not topic.valid_from:
                continue
            if topic.valid_from.tzinfo is None:
                topic.valid_from = topic.valid_from.replace(tzinfo=UTC)
            if topic.valid_from >= start_time:
                valid_topics.append(topic)
        
        if not valid_topics:
            return []
        
        # Initialize patterns list
        patterns = []
        
        # Check for repetitive narratives first
        by_category = {}
        for topic in valid_topics:
            if "category" not in topic.properties:
                continue
            cat = topic.properties["category"].value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(topic)
        
        # Look for repeated narratives in each category
        for category, topics in by_category.items():
            if len(topics) < 3:
                continue
            
            # Check for keyword matches
            for topic in topics:
                if "keywords" not in topic.properties:
                    continue
                    
                base_keywords = set(topic.properties["keywords"].value)
                matches = []
                
                for other in topics:
                    if other.id == topic.id:
                        continue
                    if "keywords" not in other.properties:
                        continue
                        
                    other_keywords = set(other.properties["keywords"].value)
                    if base_keywords == other_keywords:
                        matches.append(other)
                
                if len(matches) >= 2:
                    patterns.append({
                        "pattern_type": "narrative_repetition",
                        "category": category,
                        "topic_count": len(matches) + 1,
                        "confidence": 1.0,
                        "metadata": {
                            "base_topic_id": str(topic.id),
                            "related_topic_ids": [str(t.id) for t in matches]
                        }
                    })
                    break  # Found one pattern in this category
        
        # Check for coordinated shifts
        for topic in valid_topics:
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
                    by_target[target].add(str(trans.properties["source_entity_id"]))
            
            # Look for coordinated shifts
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
                    break  # Found one pattern for this topic
        
        # Check for emotional manipulation
        if len(valid_topics) >= 3:
            # Sort by time
            valid_topics.sort(key=lambda x: x.valid_from)
            
            # Get sentiment changes
            sentiments = []
            for topic in valid_topics:
                if "sentiment" not in topic.properties:
                    continue
                sentiments.append(topic.properties["sentiment"].value)
            
            if len(sentiments) >= 3:
                fear_change = sentiments[-1]["fear"] - sentiments[0]["fear"]
                anger_change = sentiments[-1]["anger"] - sentiments[0]["anger"]
                
                if fear_change >= 0.3 or anger_change >= 0.3:
                    patterns.append({
                        "pattern_type": "emotional_manipulation",
                        "topic_id": str(valid_topics[-1].id),
                        "confidence": max(fear_change, anger_change),
                        "metadata": {
                            "fear_change": fear_change,
                            "anger_change": anger_change,
                            "sequence_length": len(sentiments)
                        }
                    })
        
        return patterns