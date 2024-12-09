from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..types import TimeAwareEntity

class EmotionalManipulationDetector:
    def __init__(self, min_confidence: float = 0.6):
        self.min_confidence = min_confidence

    def detect_emotional_escalation(self, topics: List[TimeAwareEntity]) -> Optional[Dict]:
        if len(topics) < 3:  # Need at least 3 points for a pattern
            return None

        # Get topics with sentiment and sort by time
        valid_topics = []
        for topic in topics:
            if "sentiment" not in topic.properties:
                continue
            valid_topics.append({
                "id": topic.id,
                "time": topic.valid_from,
                "sentiment": topic.properties["sentiment"].value
            })
        
        if len(valid_topics) < 3:
            return None

        # Sort by time
        valid_topics.sort(key=lambda x: x["time"])

        # Extract sentiment sequences
        first = valid_topics[0]["sentiment"]
        last = valid_topics[-1]["sentiment"]

        # Calculate changes
        fear_change = last["fear"] - first["fear"]
        anger_change = last["anger"] - first["anger"]
        intensity_change = last["intensity"] - first["intensity"]

        # Check for significant changes
        if fear_change < 0.2 and anger_change < 0.2:
            return None

        # Calculate confidence
        confidence = max(fear_change, anger_change)
        if confidence < self.min_confidence:
            return None

        return {
            "pattern_type": "emotional_manipulation",
            "topic_id": str(valid_topics[-1]["id"]),
            "confidence": confidence,
            "metadata": {
                "escalation_count": len(valid_topics),
                "max_escalation": max(fear_change, anger_change),
                "fear_level": last["fear"],
                "anger_level": last["anger"]
            }
        }