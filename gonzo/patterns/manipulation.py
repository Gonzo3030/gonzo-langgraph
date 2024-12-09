from typing import Dict, List, Optional
from datetime import datetime, timedelta, UTC
import logging
from uuid import uuid4

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
        topics = self._get_topics_in_timeframe(timeframe)
        if not topics:
            logger.debug(f"No topics found within timeframe {timeframe}")
            return []
            
        patterns = []
        logger.debug(f"Found {len(topics)} topics within timeframe")
        
        # Detect emotional manipulation
        emotional_pattern = self._detect_emotional_manipulation(topics, timeframe)
        if emotional_pattern:
            patterns.append(emotional_pattern)
            logger.debug(f"Detected emotional manipulation pattern: {emotional_pattern}")
        
        # Detect narrative repetition and coordinated shifts
        for topic in topics:
            repetition = self._detect_narrative_repetition(topic, timeframe)
            if repetition:
                patterns.append(repetition)
                logger.debug(f"Detected narrative repetition: {repetition}")
                
            shift = self._detect_coordinated_shift(topic, timeframe)
            if shift:
                patterns.append(shift)
                logger.debug(f"Detected coordinated shift: {shift}")
        
        return patterns

    def _detect_emotional_manipulation(self, topics: List[TimeAwareEntity], timeframe: int) -> Optional[Dict]:
        try:
            pattern = self.emotional_detector.detect_emotional_escalation(topics, timeframe)
            if pattern:
                logger.debug(f"Found emotional manipulation pattern: {pattern}")
            return pattern
        except Exception as e:
            logger.error(f"Error in emotional manipulation detection: {e}", exc_info=True)
            return None

    def _get_topics_in_timeframe(self, timeframe: int) -> List[TimeAwareEntity]:
        now = datetime.now(UTC)
        start_time = now - timedelta(seconds=timeframe)
        
        logger.debug(f"Getting topics after {start_time}")
        topics = self.graph.get_entities(
            entity_type="topic",
            valid_from_after=start_time
        )
        logger.debug(f"Found {len(topics)} topics")
        return topics

    def _detect_narrative_repetition(self, topic: TimeAwareEntity, timeframe: float) -> Optional[Dict]:
        if "category" not in topic.properties:
            return None
            
        category = topic.properties["category"].value
        related = self._get_related_topics(topic, category, timeframe)

        if len(related) < 2:
            return None

        base_content = self._get_topic_content(topic)
        similar_topics = []
        similarity_scores = []

        for rel_topic in related:
            rel_content = self._get_topic_content(rel_topic)
            similarity = self._calculate_content_similarity(base_content, rel_content)
            logger.debug(f"Similarity between {topic.id} and {rel_topic.id}: {similarity}")
            
            if set(base_content["keywords"]) == set(rel_content["keywords"]):
                similar_topics.append(rel_topic)
                similarity_scores.append(1.0)
            elif similarity >= 0.7:
                similar_topics.append(rel_topic)
                similarity_scores.append(similarity)

        if not similar_topics:
            return None

        confidence = sum(similarity_scores) / len(similarity_scores)
        logger.debug(f"Narrative repetition confidence: {confidence}")

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

    def _detect_coordinated_shift(self, topic: TimeAwareEntity, timeframe: float) -> Optional[Dict]:
        transitions = self.graph.get_relationships(
            relationship_type="topic_transition",
            source_id=topic.id
        )
        
        if len(transitions) < 2:
            return None

        window_size = timedelta(minutes=15)
        clusters = self._cluster_transitions_by_time(transitions, window_size)
        
        pattern_clusters = []
        for window_start, cluster in clusters.items():
            sources = set()
            targets = set()
            for transition in cluster:
                if "source_entity_id" in transition.properties:
                    sources.add(transition.properties["source_entity_id"])
                targets.add(transition.target_id)
            
            if len(sources) >= 2 and len(targets) < len(sources):
                pattern_clusters.append({
                    "window_start": window_start.isoformat(),
                    "source_count": len(sources),
                    "transition_count": len(cluster),
                    "shared_target_count": len(targets)
                })

        if not pattern_clusters:
            return None
            
        max_cluster = max(pattern_clusters, key=lambda c: c["source_count"])
        source_ratio = max_cluster["source_count"] / len(transitions)
        target_ratio = max_cluster["shared_target_count"] / max_cluster["source_count"]
        confidence = (source_ratio * 0.7 + target_ratio * 0.3) * (1 + 0.1 * (len(pattern_clusters) - 1))
        
        logger.debug(f"Coordinated shift confidence: {confidence}")

        if confidence < self.min_confidence:
            return None

        return {
            "pattern_type": "coordinated_shift",
            "topic_id": str(topic.id),
            "timeframe": timeframe,
            "confidence": confidence,
            "metadata": {
                "clusters": pattern_clusters
            }
        }

    def _get_related_topics(self, topic: TimeAwareEntity, category: str, timeframe: float) -> List[TimeAwareEntity]:
        now = datetime.now(UTC)
        start_time = now - timedelta(seconds=timeframe)
        
        return self.graph.get_entities(
            entity_type="topic",
            valid_from_after=start_time,
            property_filters=[("category", category)]
        )

    def _get_topic_content(self, topic: TimeAwareEntity) -> Dict:
        return {
            "content": topic.properties.get("content", Property(key="content", value="")).value,
            "keywords": topic.properties.get("keywords", Property(key="keywords", value=[])).value
        }

    def _calculate_content_similarity(self, content1: Dict, content2: Dict) -> float:
        keywords1 = set(content1["keywords"])
        keywords2 = set(content2["keywords"])
        
        if not keywords1 or not keywords2:
            return 0.0
            
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union

    def _cluster_transitions_by_time(self, transitions: List[TimeAwareEntity], window_size: timedelta) -> Dict[datetime, List[TimeAwareEntity]]:
        clusters = {}
        
        for transition in transitions:
            timestamp = transition.valid_from
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
                
            window_start = timestamp.replace(minute=(timestamp.minute // 15) * 15,
                                         second=0, microsecond=0)
            
            if window_start not in clusters:
                clusters[window_start] = []
            clusters[window_start].append(transition)
            
        return clusters