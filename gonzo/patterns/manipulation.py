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