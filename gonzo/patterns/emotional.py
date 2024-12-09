from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..types import TimeAwareEntity

logger = logging.getLogger(__name__)

class EmotionalManipulationDetector:
    def __init__(self, min_confidence: float = 0.6):
        self.min_confidence = min_confidence

    def detect_emotional_escalation(self, topics: List[TimeAwareEntity]) -> Optional[Dict]:
        """Detect patterns of emotional escalation across topics."""
        if len(topics) < 3:  # Need at least 3 points to establish a pattern
            return None
            
        # Sort topics by time
        sorted_topics = sorted(topics, key=lambda x: x.valid_from)
        
        # Extract sentiment sequences
        fear_sequence = []
        anger_sequence = []
        intensity_sequence = []
        
        for topic in sorted_topics:
            if "sentiment" not in topic.properties:
                continue
                
            sentiment = topic.properties["sentiment"].value
            fear_sequence.append(sentiment["fear"])
            anger_sequence.append(sentiment["anger"])
            intensity_sequence.append(sentiment["intensity"])
            
        if not fear_sequence or not anger_sequence:
            return None
            
        # Calculate escalation metrics
        fear_escalation = fear_sequence[-1] - fear_sequence[0]
        anger_escalation = anger_sequence[-1] - anger_sequence[0]
        intensity_escalation = intensity_sequence[-1] - intensity_sequence[0]
        
        # Check for significant escalation
        if fear_escalation < 0.3 and anger_escalation < 0.3:
            return None
            
        # Calculate confidence based on multiple factors
        escalation_confidence = max(fear_escalation, anger_escalation)
        consistency = self._calculate_consistency(fear_sequence, anger_sequence)
        intensity_factor = intensity_escalation / 0.5  # Normalize to 0-1 range
        
        confidence = (
            escalation_confidence * 0.5 +
            consistency * 0.3 +
            intensity_factor * 0.2
        )
        
        if confidence < self.min_confidence:
            return None
            
        return {
            "pattern_type": "emotional_manipulation",
            "topic_id": str(sorted_topics[-1].id),
            "confidence": confidence,
            "metadata": {
                "escalation_count": len(sorted_topics),
                "max_escalation": max(fear_escalation, anger_escalation),
                "fear_level": fear_sequence[-1],
                "anger_level": anger_sequence[-1]
            }
        }
        
    def _calculate_consistency(self, fear_sequence: List[float], anger_sequence: List[float]) -> float:
        """Calculate how consistently emotions are escalating."""
        fear_changes = [fear_sequence[i] - fear_sequence[i-1] 
                       for i in range(1, len(fear_sequence))]
        anger_changes = [anger_sequence[i] - anger_sequence[i-1]
                        for i in range(1, len(anger_sequence))]
        
        # Check if changes are consistently positive
        fear_consistent = sum(1 for x in fear_changes if x > 0) / len(fear_changes)
        anger_consistent = sum(1 for x in anger_changes if x > 0) / len(anger_changes)
        
        return (fear_consistent + anger_consistent) / 2