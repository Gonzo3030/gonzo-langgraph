"""Pattern source collector and manager."""

from typing import List, Dict, Optional, Any
from datetime import datetime
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
                'extracted_at': datetime.utcnow()
            }
            
        return patterns
        
    def _process_patterns(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process transcript to extract manipulation patterns.
        
        Args:
            transcript: Video transcript data
            
        Returns:
            List of identified patterns
        """
        patterns = []
        current_segment = []
        
        # Look for key phrases indicating pattern description
        pattern_indicators = [
            "manipulation", "propaganda", "narrative",
            "mainstream media", "corporate media", "deep state",
            "pattern", "technique", "tactic"
        ]
        
        for segment in transcript:
            text = segment["text"].lower()
            
            # Check for pattern indicators
            if any(indicator in text for indicator in pattern_indicators):
                current_segment.append(segment)
            elif current_segment:
                # Process completed segment
                pattern = self._extract_pattern_from_segment(current_segment)
                if pattern:
                    patterns.append(pattern)
                current_segment = []
        
        return patterns
        
    def _extract_pattern_from_segment(self, 
        segment: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Extract pattern information from transcript segment.
        
        Args:
            segment: List of transcript segments describing a pattern
            
        Returns:
            Pattern metadata if identified, None otherwise
        """
        # Combine segment text
        text = " ".join(s["text"] for s in segment)
        
        # Basic pattern extraction
        # TODO: Enhance with NLP for better pattern identification
        return {
            "type": "manipulation_pattern",
            "description": text,
            "timestamp_start": segment[0]["start"],
            "timestamp_end": segment[-1]["start"] + segment[-1]["duration"],
            "confidence": 0.7  # TODO: Implement proper confidence scoring
        }
        
    def get_cached_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached patterns."""
        return self.pattern_cache