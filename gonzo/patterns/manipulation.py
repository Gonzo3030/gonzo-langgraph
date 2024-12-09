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
        # Get topics within timeframe
        now = datetime.now(UTC)
        start_time = now - timedelta(seconds=timeframe)
        
        topics = []
        for topic in self.graph.get_entities_by_type("topic"):
            if isinstance(topic, TimeAwareEntity) and topic.valid_from:
                if topic.valid_from >= start_time:
                    topics.append(topic)
        
        logger.debug(f"Found {len(topics)} topics in timeframe")
        if not topics:
            return []
        
        patterns = []
        for topic in topics:
            narrative = self._detect_narrative_repetition(topic, topics)
            if narrative:
                patterns.append(narrative)
                
            coordinated = self._detect_coordinated_shift(topic)
            if coordinated:
                patterns.append(coordinated)
                
            emotional = self._detect_emotional_manipulation(topics)
            if emotional:
                patterns.append(emotional)
                break  # Only need one emotional pattern per timeframe
        
        return patterns

    def _detect_narrative_repetition(self, topic: TimeAwareEntity, all_topics: List[TimeAwareEntity]) -> Optional[Dict]:
        # Basic property checks
        if "category" not in topic.properties:
            return None
        if "keywords" not in topic.properties:
            return None
            
        topic_category = topic.properties["category"].value
        topic_keywords = topic.properties["keywords"].value
        
        # Find similar topics
        similar_topics = []
        for other in all_topics:
            if other.id == topic.id:
                continue
                
            if "category" not in other.properties or other.properties["category"].value != topic_category:
                continue
                
            if "keywords" not in other.properties:
                continue
                
            other_keywords = other.properties["keywords"].value
            
            # Check for keyword similarity
            if set(topic_keywords) == set(other_keywords):
                similar_topics.append(other)
        
        if len(similar_topics) < 2:  # Need at least 2 similar topics
            return None
            
        # Since keywords match exactly, use max confidence
        return {
            "pattern_type": "narrative_repetition",
            "category": topic_category,
            "topic_count": len(similar_topics) + 1,
            "confidence": 1.0,
            "metadata": {
                "base_topic_id": str(topic.id),
                "related_topic_ids": [str(t.id) for t in similar_topics]
            }
        }

    def _detect_coordinated_shift(self, topic: TimeAwareEntity) -> Optional[Dict]:
        # Get all transitions from this topic
        transitions = self.graph.get_relationships_by_type(
            relationship_type="topic_transition",
            source_id=topic.id
        )
        
        if len(transitions) < 2:
            return None
        
        # Group by target
        target_groups = {}
        for transition in transitions:
            target_id = str(transition.target_id)
            if target_id not in target_groups:
                target_groups[target_id] = []
            target_groups[target_id].append(transition)
        
        # Look for coordinated shifts (multiple sources to same target)
        coordinated_groups = []
        for target_id, group in target_groups.items():
            sources = set()
            for transition in group:
                if "source_entity_id" in transition.properties:
                    sources.add(str(transition.properties["source_entity_id"]))
            
            if len(sources) >= 2:
                coordinated_groups.append({
                    "target_id": target_id,
                    "source_count": len(sources),
                    "source_ids": list(sources)
                })
        
        if not coordinated_groups:
            return None
            
        # Calculate confidence based on coordination
        max_group = max(coordinated_groups, key=lambda x: x["source_count"])
        confidence = max_group["source_count"] / len(transitions)
        
        if confidence < self.min_confidence:
            return None
        
        return {
            "pattern_type": "coordinated_shift",
            "topic_id": str(topic.id),
            "confidence": confidence,
            "metadata": {
                "coordinated_groups": coordinated_groups
            }
        }

    def _detect_emotional_manipulation(self, topics: List[TimeAwareEntity]) -> Optional[Dict]:
        if len(topics) < 3:
            return None
            
        # Extract sentiment sequences
        sequences = []
        for topic in topics:
            if "sentiment" not in topic.properties:
                continue
            sequences.append({
                "topic_id": str(topic.id),
                "sentiment": topic.properties["sentiment"].value,
                "valid_from": topic.valid_from
            })
        
        if len(sequences) < 3:
            return None
            
        # Sort by time
        sequences.sort(key=lambda x: x["valid_from"])
        
        # Calculate changes
        fear_change = sequences[-1]["sentiment"]["fear"] - sequences[0]["sentiment"]["fear"]
        anger_change = sequences[-1]["sentiment"]["anger"] - sequences[0]["sentiment"]["anger"]
        
        # Check for significant changes
        if fear_change < 0.3 and anger_change < 0.3:
            return None
            
        confidence = max(fear_change, anger_change)
        if confidence < self.min_confidence:
            return None
            
        return {
            "pattern_type": "emotional_manipulation",
            "topic_id": sequences[-1]["topic_id"],
            "confidence": confidence,
            "metadata": {
                "fear_change": fear_change,
                "anger_change": anger_change,
                "sequence_length": len(sequences)
            }
        }