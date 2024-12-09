from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..types import TimeAwareEntity

logger = logging.getLogger(__name__)

class EmotionalManipulationDetector:
    def __init__(self, min_confidence: float = 0.6):
        self.min_confidence = min_confidence

    def detect_emotional_escalation(self, topics: List[TimeAwareEntity]) -> Optional[Dict]:
        logger.debug(f"Starting emotional analysis with {len(topics)} topics")

        if len(topics) < 3:
            logger.debug("Not enough topics for pattern")
            return None

        # Sort topics by time first
        sorted_topics = sorted(topics, key=lambda x: x.valid_from)
        logger.debug(f"Sorted topics by time")

        # Extract sentiment sequences
        sequence = []
        for topic in sorted_topics:
            if "sentiment" not in topic.properties:
                logger.debug(f"Topic {topic.id} missing sentiment")
                continue
                
            sentiment = topic.properties["sentiment"].value
            sequence.append({
                "id": topic.id,
                "sentiment": sentiment,
                "time": topic.valid_from
            })

        logger.debug(f"Found {len(sequence)} topics with sentiment")
        if len(sequence) < 3:
            logger.debug("Not enough topics with sentiment data")
            return None

        # Calculate changes
        first = sequence[0]["sentiment"]
        last = sequence[-1]["sentiment"]

        fear_change = last["fear"] - first["fear"]
        anger_change = last["anger"] - first["anger"]

        logger.debug(f"Fear change: {fear_change}, Anger change: {anger_change}")

        # Both fear and anger should show escalation
        if fear_change <= 0.3 and anger_change <= 0.3:
            logger.debug("Changes too small to indicate manipulation")
            return None

        max_change = max(fear_change, anger_change)
        logger.debug(f"Max emotional change: {max_change}")

        if max_change < self.min_confidence:
            logger.debug(f"Confidence {max_change} below threshold {self.min_confidence}")
            return None

        pattern = {
            "pattern_type": "emotional_manipulation",
            "topic_id": str(sequence[-1]["id"]),
            "confidence": max_change,
            "metadata": {
                "escalation_count": len(sequence),
                "max_escalation": max_change,
                "fear_level": last["fear"],
                "anger_level": last["anger"]
            }
        }
        logger.debug(f"Found emotional pattern: {pattern}")
        return pattern