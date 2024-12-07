"""Pattern source collector and manager."""

from typing import List, Dict, Optional, Any
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
        pattern_indicators = {
            "soft_propaganda": [
                "manipulation", "propaganda", "narrative",
                "mainstream media", "corporate media", "deep state",
                "legacy media", "pattern", "technique", "tactic"
            ],
            "fear_tactics": [
                "fear", "panic", "threat", "danger", "crisis",
                "emergency", "catastrophe", "disaster"
            ],
            "economic_manipulation": [
                "inflation", "economy", "economic", "transitory",
                "market", "financial", "cost", "price", "crisis"
            ]
        }
        
        for segment in transcript:
            text = segment["text"].lower()
            pattern_found = False
            
            # Check for pattern indicators by category
            for pattern_type, indicators in pattern_indicators.items():
                if any(indicator in text for indicator in indicators):
                    if not current_segment:
                        current_segment.append({"type": pattern_type})
                    current_segment.append(segment)
                    pattern_found = True
                    break
            
            if not pattern_found and current_segment:
                # Process completed segment
                pattern = self._extract_pattern_from_segment(current_segment)
                if pattern:
                    patterns.append(pattern)
                current_segment = []
        
        # Process any remaining segment
        if current_segment:
            pattern = self._extract_pattern_from_segment(current_segment)
            if pattern:
                patterns.append(pattern)
        
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
        if len(segment) < 2:  # Need type info and at least one content segment
            return None
            
        pattern_type = segment[0]["type"]
        content_segments = segment[1:]  # Skip the type info
        
        # Combine segment text
        text = " ".join(s["text"] for s in content_segments)
        
        return {
            "type": "manipulation_pattern",
            "pattern_category": pattern_type,
            "description": text,
            "timestamp_start": content_segments[0]["start"],
            "timestamp_end": content_segments[-1]["start"] + content_segments[-1]["duration"],
            "confidence": 0.7  # TODO: Implement proper confidence scoring
        }
        
    def get_cached_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached patterns."""
        return self.pattern_cache