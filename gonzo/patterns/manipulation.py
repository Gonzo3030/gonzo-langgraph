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

    def detect_narrative_manipulation(self, timeframe: float = 3600) -> List[Dict]:
        patterns = []
        topics = self._get_topics_in_timeframe(timeframe)
        if not topics:
            return patterns

        for topic in topics:
            repetition = self._detect_narrative_repetition(topic, timeframe)
            if repetition:
                patterns.append(repetition)

            shift = self._detect_coordinated_shifts(topic, timeframe)
            if shift:
                patterns.append(shift)

            emotional = self._detect_emotional_manipulation(topic, timeframe)
            if emotional:
                patterns.append(emotional)

        return patterns

    def _get_topics_in_timeframe(self, timeframe: float) -> List[TimeAwareEntity]:
        now = datetime.now(UTC)
        topics = self.graph.get_entities_by_type("topic")
        return [
            topic for topic in topics 
            if not self._is_outside_timeframe(topic, now, timeframe)
        ]

    def _detect_narrative_repetition(self, topic: TimeAwareEntity, timeframe: float) -> Optional[Dict]:
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
            if similarity > 0.5:
                similar_topics.append(rel_topic)
                similarity_scores.append(similarity)

        if not similar_topics:
            return None

        return {
            "pattern_type": "narrative_repetition",
            "category": category,
            "topic_count": len(similar_topics) + 1,
            "confidence": sum(similarity_scores) / len(similarity_scores),
            "metadata": {
                "base_topic_id": str(topic.id),
                "related_topic_ids": [str(t.id) for t in similar_topics],
                "similarity_scores": similarity_scores
            }
        }

    def _get_topic_content(self, topic: TimeAwareEntity) -> Dict:
        return {
            "title": topic.properties.get("title", Property(key="title", value="")).value,
            "content": topic.properties.get("content", Property(key="content", value="")).value,
            "sentiment": topic.properties.get("sentiment", Property(key="sentiment", value={})).value,
            "keywords": topic.properties.get("keywords", Property(key="keywords", value=[])).value
        }