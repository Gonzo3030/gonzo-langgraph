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

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensure a datetime is UTC-aware."""
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    def detect_narrative_manipulation(self, timeframe: int = 3600) -> List[Dict]:
        now = datetime.now(UTC)  # Use UTC explicitly for base time
        start_time = now - timedelta(seconds=timeframe)
        
        # Get all topics and manually filter by time to avoid timezone issues
        all_topics = self.graph.get_entities_by_type("topic")
        topics = [t for t in all_topics 
                 if isinstance(t, TimeAwareEntity) and
                 t.valid_from and 
                 self._ensure_utc(t.valid_from) >= start_time]
        
        if not topics:
            return []
            
        patterns = []
        
        # Detect emotional manipulation first
        emotional_pattern = self._detect_emotional_manipulation(topics)
        if emotional_pattern:
            patterns.append(emotional_pattern)
        
        # Then detect narrative patterns
        for topic in topics:
            repetition = self._detect_narrative_repetition(topic)
            if repetition:
                patterns.append(repetition)
                
            shift = self._detect_coordinated_shift(topic)
            if shift:
                patterns.append(shift)
        
        return patterns

    def _detect_emotional_manipulation(self, topics: List[TimeAwareEntity]) -> Optional[Dict]:
        return self.emotional_detector.detect_emotional_escalation(topics)

    def _detect_narrative_repetition(self, topic: TimeAwareEntity) -> Optional[Dict]:
        if "category" not in topic.properties or "keywords" not in topic.properties:
            return None
            
        category = topic.properties["category"].value
        related = [t for t in self.graph.get_entities_by_type("topic")
                  if "category" in t.properties and
                  "keywords" in t.properties and
                  t.id != topic.id and
                  t.properties["category"].value == category]

        if len(related) < 2:
            return None

        base_content = self._get_topic_content(topic)
        similar_topics = []
        similarity_scores = []

        for rel_topic in related:
            rel_content = self._get_topic_content(rel_topic)
            similarity = self._calculate_content_similarity(base_content, rel_content)
            
            # Lower the similarity threshold to catch more patterns
            if similarity >= 0.5:
                similar_topics.append(rel_topic)
                similarity_scores.append(similarity)

        if not similar_topics:
            return None

        confidence = sum(similarity_scores) / len(similarity_scores)
        if confidence < self.min_confidence:
            return None

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

    def _detect_coordinated_shift(self, topic: TimeAwareEntity) -> Optional[Dict]:
        transitions = self.graph.get_relationships_by_type(
            relationship_type="topic_transition",
            source_id=topic.id
        )
        
        if len(transitions) < 2:
            return None

        # Group transitions by 15-minute windows
        clusters = {}
        for transition in transitions:
            if not hasattr(transition, 'valid_from'):
                continue
                
            timestamp = self._ensure_utc(transition.valid_from)
            window_start = timestamp.replace(
                minute=(timestamp.minute // 15) * 15,
                second=0,
                microsecond=0
            )
            
            if window_start not in clusters:
                clusters[window_start] = []
            clusters[window_start].append(transition)
            
        if not clusters:
            return None

        pattern_clusters = []
        for window_start, cluster in clusters.items():
            sources = set()
            targets = set()
            for transition in cluster:
                if "source_entity_id" in transition.properties:
                    sources.add(str(transition.properties["source_entity_id"]))
                targets.add(str(transition.target_id))
            
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
        # Combine ratios to get better confidence score
        confidence = (source_ratio * 0.7 + target_ratio * 0.3) * (1 + 0.1 * (len(transitions) - 1))

        if confidence < self.min_confidence:
            return None

        return {
            "pattern_type": "coordinated_shift",
            "topic_id": str(topic.id),
            "confidence": confidence,
            "metadata": {
                "clusters": pattern_clusters
            }
        }

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