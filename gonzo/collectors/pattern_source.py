"""Pattern source collector and manager."""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, UTC
import logging
from .youtube import YouTubeCollector

logger = logging.getLogger(__name__)

class PatternSourceManager:
    """Manages sources for propaganda and manipulation patterns."""
    
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
        pattern_indicators = {
            "fear_tactics": [
                "fear", "panic", "threat", "danger", "crisis",
                "emergency", "catastrophe", "disaster"
            ],
            "economic_manipulation": [
                "inflation", "economy", "economic", "transitory",
                "market", "financial", "cost", "price"
            ],
            "soft_propaganda": [
                "manipulation", "propaganda", "narrative",
                "mainstream media", "corporate media", "deep state",
                "legacy media"
            ]
        }
        
        # Score each pattern type
        scores = {}
        text = text.lower()
        
        for pattern_type, indicators in pattern_indicators.items():
            count = sum(1 for indicator in indicators if indicator in text)
            if count > 0:
                scores[pattern_type] = count / len(indicators)
        
        if scores:
            # Return the highest scoring pattern type
            best_type = max(scores.items(), key=lambda x: x[1])
            return best_type[0], best_type[1]
        
        return None
        
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
        
        for segment in transcript:
            text = segment["text"]
            pattern_info = self._detect_pattern_type(text)
            
            if pattern_info:
                pattern_type, confidence = pattern_info
                if not current_segment:
                    # Start new segment
                    current_type = pattern_type
                    current_segment = [segment]
                elif pattern_type == current_type:
                    # Continue current segment
                    current_segment.append(segment)
                else:
                    # Process current segment and start new one
                    pattern = self._extract_pattern_from_segment(current_segment, current_type)
                    if pattern:
                        patterns.append(pattern)
                    current_type = pattern_type
                    current_segment = [segment]
            elif current_segment:
                # Process completed segment
                pattern = self._extract_pattern_from_segment(current_segment, current_type)
                if pattern:
                    patterns.append(pattern)
                current_segment = []
                current_type = None
        
        # Process any remaining segment
        if current_segment:
            pattern = self._extract_pattern_from_segment(current_segment, current_type)
            if pattern:
                patterns.append(pattern)
        
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