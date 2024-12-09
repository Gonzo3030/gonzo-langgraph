from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from statistics import mean, stdev
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmotionalPattern:
    """Represents a detected emotional manipulation pattern."""
    start_time: datetime
    end_time: datetime
    emotion_type: str
    intensity_change: float
    confidence: float
    topic_ids: List[str]

class EmotionalManipulationDetector:
    """Detects patterns of emotional manipulation in content."""
    
    def __init__(self, min_intensity_change: float = 0.3,
                 min_confidence: float = 0.6):
        self.min_intensity_change = min_intensity_change
        self.min_confidence = min_confidence
    
    def detect_emotional_escalation(self, topics: List[Dict], timeframe: int) -> Optional[Dict]:
        """
        Detect patterns of emotional escalation across topics.
        
        Args:
            topics: List of topic entities with sentiment data
            timeframe: Time window in seconds to analyze
        
        Returns:
            Dict containing pattern data if detected, None otherwise
        """
        if len(topics) < 3:  # Need at least 3 points to establish a pattern
            return None
            
        # Sort topics by timestamp
        sorted_topics = sorted(topics, key=lambda x: x.valid_from)
        
        # Extract emotion sequences
        fear_sequence = [t.properties["sentiment"].value["fear"] for t in sorted_topics]
        anger_sequence = [t.properties["sentiment"].value["anger"] for t in sorted_topics]
        intensity_sequence = [t.properties["sentiment"].value["intensity"] for t in sorted_topics]
        
        # Calculate trends
        fear_trend = self._calculate_trend(fear_sequence)
        anger_trend = self._calculate_trend(anger_sequence)
        intensity_trend = self._calculate_trend(intensity_sequence)
        
        # Check for significant escalation
        patterns = []
        if fear_trend > self.min_intensity_change:
            patterns.append(("fear", fear_trend))
        if anger_trend > self.min_intensity_change:
            patterns.append(("anger", anger_trend))
            
        if not patterns:
            return None
            
        # Calculate confidence based on consistency and intensity
        strongest_pattern = max(patterns, key=lambda x: x[1])
        emotion_type, trend = strongest_pattern
        
        confidence = self._calculate_confidence(
            trend,
            intensity_trend,
            len(sorted_topics)
        )
        
        if confidence < self.min_confidence:
            return None
            
        return {
            "pattern_type": "emotional_manipulation",
            "emotion_type": emotion_type,
            "intensity_change": trend,
            "timeframe": timeframe,
            "confidence": confidence,
            "metadata": {
                "topic_ids": [str(t.id) for t in sorted_topics],
                "start_time": sorted_topics[0].valid_from.isoformat(),
                "end_time": sorted_topics[-1].valid_from.isoformat()
            }
        }
    
    def _calculate_trend(self, sequence: List[float]) -> float:
        """Calculate the overall trend in a sequence of values."""
        if not sequence:
            return 0.0
        return sequence[-1] - sequence[0]
    
    def _calculate_confidence(self, emotion_trend: float,
                            intensity_trend: float,
                            sample_size: int) -> float:
        """
        Calculate confidence score for detected pattern.
        
        Factors:
        - Magnitude of emotional change
        - Correlation with overall intensity
        - Sample size
        """
        # Base confidence from emotion trend
        base_confidence = min(1.0, emotion_trend / self.min_intensity_change)
        
        # Adjust for intensity correlation
        intensity_factor = min(1.0, intensity_trend / self.min_intensity_change)
        
        # Adjust for sample size (more samples = higher confidence)
        size_factor = min(1.0, (sample_size - 2) / 3)  # -2 because we need at least 3
        
        # Combine factors with weights
        confidence = (
            base_confidence * 0.5 +
            intensity_factor * 0.3 +
            size_factor * 0.2
        )
        
        return confidence