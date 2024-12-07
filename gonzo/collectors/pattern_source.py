"""Pattern source collector and manager."""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, UTC
import logging
from collections import Counter

from .youtube import YouTubeCollector

logger = logging.getLogger(__name__)

class PatternSourceManager:
    """Manages sources for propaganda and manipulation patterns."""
    
    # Pattern indicators with their priorities and required matches
    PATTERN_INDICATORS = {
        "fear_tactics": {
            "words": [
                "fear", "panic", "threat", "danger", "crisis",
                "emergency", "catastrophe", "disaster", "pandemic",
                "experimental", "risk", "unsafe"
            ],
            "priority": 3,
            "required_matches": 1  # Need at least one fear-related word
        },
        "economic_manipulation": {
            "words": [
                "inflation", "economy", "economic", "transitory",
                "market", "financial", "cost", "price", "currency",
                "dollar", "money", "recession", "wages", "markets",
                "prices", "costs", "economic indicators"
            ],
            "priority": 2,
            "required_matches": 2  # Need at least two economic terms
        },
        "soft_propaganda": {
            "words": [
                "manipulation", "propaganda", "narrative",
                "mainstream media", "corporate media", "deep state",
                "legacy media", "media", "coverage"
            ],
            "priority": 1,
            "required_matches": 1
        }
    }
    
    def __init__(self):
        self.youtube_collector = YouTubeCollector()
        self.pattern_cache: Dict[str, Dict[str, Any]] = {}
        
    def extract_patterns_from_video(self, video_url: str) -> List[Dict[str, Any]]:
        """Extract manipulation patterns from a video.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            List of identified patterns with metadata
        """
        video_id = self.youtube_collector.extract_video_id(video_url)
        if not video_id:
            logger.error(f"Invalid YouTube URL: {video_url}")
            return []
            
        # Get transcript
        transcript = self.youtube_collector.get_video_transcript(video_id)
        if not transcript:
            return []
            
        # Process and cache patterns
        patterns = self._process_patterns(transcript)
        if patterns:
            self.pattern_cache[video_id] = {
                'url': video_url,
                'patterns': patterns,
                'extracted_at': datetime.now(UTC)
            }
            
        return patterns
        
    def _detect_pattern_type(self, text: str) -> Optional[Tuple[str, float]]:
        """Detect pattern type from text with confidence score.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (pattern_type, confidence) if found, None otherwise
        """
        text = text.lower()
        scores = {}
        
        # Count matches for each pattern type
        for pattern_type, info in self.PATTERN_INDICATORS.items():
            # Count how many unique words match
            word_matches = sum(1 for word in info["words"] if word.lower() in text)
            
            # Only consider patterns that meet minimum required matches
            if word_matches >= info["required_matches"]:
                # Calculate score based on matches and priority
                base_score = word_matches / len(info["words"])
                priority_multiplier = info["priority"]
                scores[pattern_type] = base_score * priority_multiplier
        
        if not scores:
            return None
            
        # Get the pattern type with highest score
        best_type = max(scores.items(), key=lambda x: x[1])
        return best_type[0], min(1.0, best_type[1])  # Cap confidence at 1.0
        
    def _process_patterns(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process transcript to extract manipulation patterns.
        
        Args:
            transcript: Video transcript data
            
        Returns:
            List of identified patterns
        """
        patterns = []
        current_segment = []
        current_type = None
        
        def process_current_segment():
            if current_segment and current_type:
                pattern = self._extract_pattern_from_segment(current_segment, current_type)
                if pattern:
                    patterns.append(pattern)
            return [], None
        
        for segment in transcript:
            text = segment["text"]
            pattern_info = self._detect_pattern_type(text)
            
            if pattern_info:
                pattern_type, confidence = pattern_info
                if not current_segment or pattern_type == current_type:
                    # Continue or start new segment
                    current_type = pattern_type
                    current_segment.append(segment)
                else:
                    # Different pattern type found, process current segment
                    current_segment, current_type = process_current_segment()
                    current_type = pattern_type
                    current_segment = [segment]
            elif current_segment:
                # No pattern found, process any existing segment
                current_segment, current_type = process_current_segment()
        
        # Process any remaining segment
        if current_segment:
            process_current_segment()
        
        return patterns
        
    def _extract_pattern_from_segment(self, 
        segment: List[Dict[str, Any]],
        pattern_type: str
    ) -> Optional[Dict[str, Any]]:
        """Extract pattern information from transcript segment.
        
        Args:
            segment: List of transcript segments describing a pattern
            pattern_type: Type of pattern detected
            
        Returns:
            Pattern metadata if identified, None otherwise
        """
        if not segment:
            return None
            
        # Combine segment text
        text = " ".join(s["text"] for s in segment)
        
        return {
            "type": "manipulation_pattern",
            "pattern_category": pattern_type,
            "description": text,
            "timestamp_start": segment[0]["start"],
            "timestamp_end": segment[-1]["start"] + segment[-1]["duration"],
            "confidence": 0.7  # TODO: Implement better confidence scoring
        }
        
    def get_cached_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached patterns."""
        return self.pattern_cache