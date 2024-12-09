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
        all_topics = self.graph.get_entities_by_type("topic")
        
        topics = []
        for topic in all_topics:
            if not isinstance(topic, TimeAwareEntity) or not topic.valid_from:
                continue
            topic_time = self._ensure_utc(topic.valid_from)
            if topic_time >= start_time:
                topics.append(topic)
        
        if not topics:
            return []
            
        patterns = []
        
        # First detect emotional patterns which need all topics
        emotional = self._detect_emotional_manipulation(topics)
        if emotional:
            patterns.append(emotional)
        
        # Then look for individual topic patterns
        for topic in topics:
            repetition = self._detect_narrative_repetition(topic, topics)
            if repetition:
                patterns.append(repetition)
                
            shift = self._detect_coordinated_shift(topic, topics)
            if shift:
                patterns.append(shift)
        
        return patterns

    def _ensure_utc(self, dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    def _detect_emotional_manipulation(self, topics: List[TimeAwareEntity]) -> Optional[Dict]:
        # Sort topics by time
        sorted_topics = sorted(topics, key=lambda x: x.valid_from)
        
        # Track emotional changes
        sequences = []
        for topic in sorted_topics:
            if "sentiment" not in topic.properties:
                continue
            sentiment = topic.properties["sentiment"].value
            sequences.append(sentiment)
            
        if len(sequences) < 3:
            return None
            
        # Calculate emotional escalation
        first = sequences[0]
        last = sequences[-1]
        
        fear_change = last["fear"] - first["fear"]
        anger_change = last["anger"] - first["anger"]
        intensity_change = last["intensity"] - first["intensity"]
        
        if fear_change < 0.2 and anger_change < 0.2:
            return None
            
        confidence = (fear_change + anger_change + intensity_change) / 3
        
        if confidence < self.min_confidence:
            return None
            
        return {
            "pattern_type": "emotional_manipulation",
            "topic_id": str(sorted_topics[-1].id),
            "confidence": confidence,
            "metadata": {
                "escalation_count": len(sequences),
                "max_escalation": max(fear_change, anger_change),
                "fear_level": last["fear"],
                "anger_level": last["anger"]
            }
        }

    def _detect_narrative_repetition(self, topic: TimeAwareEntity, all_topics: List[TimeAwareEntity]) -> Optional[Dict]:
        if "category" not in topic.properties or "keywords" not in topic.properties:
            return None
            
        category = topic.properties["category"].value
        base_keywords = set(topic.properties["keywords"].value)
        
        similar_topics = []
        similarity_scores = []
        
        for other in all_topics:
            if other.id == topic.id:
                continue
                
            if "category" not in other.properties or "keywords" not in other.properties:
                continue
                
            if other.properties["category"].value != category:
                continue
                
            other_keywords = set(other.properties["keywords"].value)
            
            # For identical keywords, assign perfect similarity
            if base_keywords == other_keywords:
                similar_topics.append(other)
                similarity_scores.append(1.0)
                continue
                
            # Calculate Jaccard similarity
            intersection = len(base_keywords.intersection(other_keywords))
            union = len(base_keywords.union(other_keywords))
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= 0.5:
                similar_topics.append(other)
                similarity_scores.append(similarity)
        
        if len(similar_topics) < 2:
            return None
            
        confidence = sum(similarity_scores) / len(similarity_scores)
        
        return {
            "pattern_type": "narrative_repetition",
            "category": category,
            "topic_count": len(similar_topics) + 1,
            "confidence": confidence,
            "metadata": {
                "base_topic_id": str(topic.id),
                "related_topic_ids": [str(t.id) for t in similar_topics],
                "similarity_scores": similarity_scores
            }
        }

    def _detect_coordinated_shift(self, topic: TimeAwareEntity, all_topics: List[TimeAwareEntity]) -> Optional[Dict]:
        # Get transitions for this topic
        transitions = self.graph.get_relationships_by_type(
            relationship_type="topic_transition",
            source_id=topic.id
        )
        
        if len(transitions) < 2:
            return None
        
        # Group transitions by time window
        windows = {}
        for transition in transitions:
            # Skip if we can't determine timing
            if not hasattr(transition, "valid_from") or not transition.valid_from:
                continue
                
            # Normalize to 15-minute windows
            time = self._ensure_utc(transition.valid_from)
            window = time.replace(minute=(time.minute // 15) * 15,
                                second=0, microsecond=0)
            
            if window not in windows:
                windows[window] = []
            windows[window].append(transition)
        
        if not windows:
            return None
        
        # Look for coordinated shifts in each window
        clusters = []
        for window_start, transitions in windows.items():
            sources = set()
            targets = set()
            
            for t in transitions:
                if "source_entity_id" in t.properties:
                    sources.add(str(t.properties["source_entity_id"]))
                if hasattr(t, "target_id"):
                    targets.add(str(t.target_id))
            
            if len(sources) >= 2 and len(targets) < len(sources):
                clusters.append({
                    "window_start": window_start.isoformat(),
                    "source_count": len(sources),
                    "transition_count": len(transitions),
                    "shared_target_count": len(targets)
                })
        
        if not clusters:
            return None
            
        # Calculate confidence based on coordination metrics
        max_cluster = max(clusters, key=lambda x: x["source_count"])
        confidence = max_cluster["source_count"] / max_cluster["transition_count"]
        
        if confidence < self.min_confidence:
            return None
        
        return {
            "pattern_type": "coordinated_shift",
            "topic_id": str(topic.id),
            "confidence": confidence,
            "metadata": {
                "clusters": clusters
            }
        }