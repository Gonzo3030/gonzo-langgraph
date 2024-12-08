"""Manipulation and propaganda pattern detection."""

import logging
from datetime import datetime, UTC
from typing import List, Dict, Optional, Set
from uuid import UUID

from ..patterns.detector import PatternDetector
from ..graph.knowledge.graph import KnowledgeGraph
from ..types import TimeAwareEntity, Relationship, Property

logger = logging.getLogger(__name__)

class ManipulationDetector(PatternDetector):
    def __init__(self, graph: KnowledgeGraph):
        super().__init__(graph)
        self._manipulation_patterns = {}

    def _get_topics_in_timeframe(self, timeframe: float) -> List[TimeAwareEntity]:
        """Get topics within the specified timeframe.

        Args:
            timeframe: Time window in seconds to look back from now

        Returns:
            List of topics within the timeframe
        """
        now = datetime.now(UTC)
        topics = self.graph.get_entities_by_type("topic")
        
        valid_topics = [
            topic for topic in topics
            if topic.valid_from and (now - topic.valid_from).total_seconds() <= timeframe
        ]
        
        logger.debug(f"Found {len(valid_topics)} topics within timeframe")
        return valid_topics

    def detect_narrative_manipulation(self, timeframe: float = 3600) -> List[Dict]:
        """Detect various types of narrative manipulation patterns.

        Args:
            timeframe: Time window in seconds to analyze (default: 1 hour)

        Returns:
            List of detected manipulation patterns
        """
        patterns = []
        topics = self._get_topics_in_timeframe(timeframe)
        if not topics:
            logger.debug("No topics found in timeframe")
            return patterns

        # Sort topics by time to ensure consistent base topic selection
        topics.sort(key=lambda x: x.valid_from if x.valid_from else datetime.max.replace(tzinfo=UTC))

        for topic in topics:
            repetition = self._detect_narrative_repetition(topic, timeframe)
            if repetition:
                patterns.append(repetition)
                logger.debug(f"Detected narrative repetition: {repetition}")

            shift = self._detect_coordinated_shifts(topic, timeframe)
            if shift:
                patterns.append(shift)
                logger.debug(f"Detected coordinated shift: {shift}")

            emotional = self._detect_emotional_manipulation(topic, timeframe)
            if emotional:
                patterns.append(emotional)
                logger.debug(f"Detected emotional manipulation: {emotional}")

        return patterns

    def _detect_narrative_repetition(self, topic: TimeAwareEntity, timeframe: float) -> Optional[Dict]:
        """Detect repeated narratives across topics."""
        if "category" not in topic.properties:
            return None
            
        category = topic.properties["category"].value
        related = self._get_related_topics(topic, category, timeframe)

        if len(related) < 2:
            return None

        base_content = self._get_topic_content(topic)
        similar_topics = []
        similarity_scores = []

        logger.debug(f"Analyzing topic {topic.id} for narrative repetition")
        logger.debug(f"Base content keywords: {base_content['keywords']}")

        for rel_topic in related:
            rel_content = self._get_topic_content(rel_topic)
            similarity = self._calculate_content_similarity(base_content, rel_content)
            logger.debug(f"Similarity with {rel_topic.id}: {similarity}")
            logger.debug(f"Related keywords: {rel_content['keywords']}")
            
            if similarity >= 0.7:
                similar_topics.append(rel_topic)
                similarity_scores.append(similarity)

        if not similar_topics:
            return None

        confidence = sum(similarity_scores) / len(similarity_scores)
        logger.debug(f"Found narrative repetition with confidence {confidence}")

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

    def _detect_emotional_manipulation(self, topic: TimeAwareEntity, timeframe: float) -> Optional[Dict]:
        """Detect patterns of emotional manipulation in content."""
        content = self._get_topic_content(topic)
        sentiment_data = content["sentiment"]
        
        if not sentiment_data or not isinstance(sentiment_data, dict):
            return None

        related = self._get_related_topics(topic, topic.properties["category"].value, timeframe)
        emotion_trends = []

        for rel_topic in related:
            rel_content = self._get_topic_content(rel_topic)
            rel_sentiment = rel_content["sentiment"]
            if rel_sentiment and isinstance(rel_sentiment, dict):
                emotion_trends.append(rel_sentiment)

        base_intensity = float(sentiment_data.get("intensity", 0.0))
        fear_level = float(sentiment_data.get("fear", 0.0))
        anger_level = float(sentiment_data.get("anger", 0.0))

        escalation = [
            float(trend.get("intensity", 0.0)) - base_intensity
            for trend in emotion_trends
            if float(trend.get("intensity", 0.0)) > base_intensity
        ]

        if not escalation:
            return None

        intensity_factor = base_intensity * 0.4
        escalation_factor = (sum(escalation) / len(escalation)) * 0.3
        emotion_mix_factor = (fear_level + anger_level) * 0.3

        confidence = intensity_factor + escalation_factor + emotion_mix_factor

        if confidence < 0.6:
            return None

        return {
            "pattern_type": "emotional_manipulation",
            "topic_id": str(topic.id),
            "timeframe": timeframe,
            "confidence": confidence,
            "metadata": {
                "base_emotions": sentiment_data,
                "escalation_count": len(escalation),
                "max_escalation": max(escalation),
                "fear_level": fear_level,
                "anger_level": anger_level
            }
        }

    def _detect_coordinated_shifts(self, topic: TimeAwareEntity, timeframe: float) -> Optional[Dict]:
        """Detect coordinated narrative shifts across sources."""
        transitions = self.graph.get_relationships_by_type(
            "topic_transition",
            source_id=topic.id
        )

        if not transitions:
            return None

        # Group transitions by 5-minute windows
        windows = {}
        for trans in transitions:
            window_start = trans.created_at.replace(
                minute=trans.created_at.minute // 5 * 5,
                second=0,
                microsecond=0
            )
            if window_start not in windows:
                windows[window_start] = []
            windows[window_start].append(trans)

        coordinated_clusters = []
        for window_start, window_transitions in windows.items():
            if len(window_transitions) < 3:
                continue

            sources = self._get_unique_sources(window_transitions)
            if len(sources) < 2:
                continue

            shared_targets = self._get_shared_targets(window_transitions)
            if not shared_targets:
                continue

            coordinated_clusters.append({
                "window_start": window_start,
                "transitions": window_transitions,
                "sources": list(sources),
                "shared_targets": list(shared_targets)
            })

        if not coordinated_clusters:
            return None

        cluster_confidences = []
        for cluster in coordinated_clusters:
            source_diversity = len(cluster["sources"]) / 10
            target_alignment = len(cluster["shared_targets"]) / len(cluster["transitions"])
            timing_density = len(cluster["transitions"]) / 300
            confidence = min((source_diversity + target_alignment + timing_density) / 3, 0.95)
            cluster_confidences.append(confidence)

        return {
            "pattern_type": "coordinated_shift",
            "topic_id": str(topic.id),
            "timeframe": timeframe,
            "confidence": max(cluster_confidences),
            "metadata": {
                "clusters": [
                    {
                        "window_start": c["window_start"].isoformat(),
                        "source_count": len(c["sources"]),
                        "transition_count": len(c["transitions"]),
                        "shared_target_count": len(c["shared_targets"])
                    }
                    for c in coordinated_clusters
                ]
            }
        }

    def _get_topic_content(self, topic: TimeAwareEntity) -> Dict:
        """Extract relevant content from a topic entity."""
        result = {}
        props = topic.properties
        
        result["title"] = props["title"].value if "title" in props else ""
        result["content"] = props["content"].value if "content" in props else ""
        result["sentiment"] = props["sentiment"].value if "sentiment" in props else {}
        result["keywords"] = props["keywords"].value if "keywords" in props else []
        
        return result

    def _calculate_content_similarity(self, content1: Dict, content2: Dict) -> float:
        """Calculate similarity between two pieces of content."""
        keywords1 = set(content1.get("keywords", []))
        keywords2 = set(content2.get("keywords", []))

        if not keywords1 or not keywords2:
            return 0.0

        overlap = len(keywords1.intersection(keywords2))
        total = len(keywords1.union(keywords2))

        # Perfect match when all keywords are identical
        if overlap == total and overlap > 0:
            return 1.0

        return overlap / total if total > 0 else 0.0

    def _get_unique_sources(self, transitions: List[Relationship]) -> Set[UUID]:
        """Get unique source entities from transitions."""
        return {
            UUID(str(t.properties["source_entity_id"].value))
            for t in transitions
            if "source_entity_id" in t.properties
        }

    def _get_shared_targets(self, transitions: List[Relationship]) -> Set[UUID]:
        """Get targets shared by multiple transitions."""
        target_counts = {}
        for trans in transitions:
            target_id = trans.target_id
            target_counts[target_id] = target_counts.get(target_id, 0) + 1

        return {
            target_id
            for target_id, count in target_counts.items()
            if count > 1
        }

    def _get_related_topics(self, topic: TimeAwareEntity, category: str, timeframe: float) -> List[TimeAwareEntity]:
        """Get topics related to the given topic within timeframe."""
        now = datetime.now(UTC)
        topics = self.graph.get_entities_by_type("topic")

        return [
            t for t in topics
            if (t.id != topic.id and
                "category" in t.properties and
                t.properties["category"].value == category and
                t.valid_from and
                (now - t.valid_from).total_seconds() <= timeframe)
        ]