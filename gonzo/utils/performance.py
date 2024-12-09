"""Performance monitoring utilities."""

from typing import Dict, Any, Optional
from datetime import datetime
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    video_id: str
    transcript_length: int
    processing_time: float
    num_entities: int
    num_segments: int
    num_patterns: int
    entity_confidence: float
    segment_confidence: float
    pattern_confidence: float
    error_count: int

class PerformanceMonitor:
    """Monitor and track analysis performance."""
    
    def __init__(self):
        self.metrics = {}
    
    def start_analysis(self, video_id: str) -> None:
        """Start tracking analysis of a video.
        
        Args:
            video_id: YouTube video ID
        """
        self.metrics[video_id] = {
            'start_time': time.time(),
            'errors': 0
        }
    
    def log_error(self, video_id: str) -> None:
        """Log an error occurrence.
        
        Args:
            video_id: YouTube video ID
        """
        if video_id in self.metrics:
            self.metrics[video_id]['errors'] += 1
    
    def end_analysis(self,
        video_id: str,
        results: Dict[str, Any]
    ) -> PerformanceMetrics:
        """Complete analysis tracking and return metrics.
        
        Args:
            video_id: YouTube video ID
            results: Analysis results
            
        Returns:
            PerformanceMetrics object
        """
        if video_id not in self.metrics:
            logger.error(f"No start time found for video {video_id}")
            return None
            
        elapsed = time.time() - self.metrics[video_id]['start_time']
        
        # Calculate average confidences
        entity_conf = sum(e.properties.get('confidence', 0.0) 
                         for e in results.get('entities', []))
        segment_conf = sum(s.properties.get('confidence', 0.0)
                          for s in results.get('segments', []))
        pattern_conf = sum(p.get('confidence', 0.0)
                          for p in results.get('patterns', []))
        
        # Get counts
        num_entities = len(results.get('entities', []))
        num_segments = len(results.get('segments', []))
        num_patterns = len(results.get('patterns', []))
        
        # Calculate averages
        entity_conf = entity_conf / num_entities if num_entities > 0 else 0
        segment_conf = segment_conf / num_segments if num_segments > 0 else 0
        pattern_conf = pattern_conf / num_patterns if num_patterns > 0 else 0
        
        metrics = PerformanceMetrics(
            video_id=video_id,
            transcript_length=len(results.get('transcript', [])),
            processing_time=elapsed,
            num_entities=num_entities,
            num_segments=num_segments,
            num_patterns=num_patterns,
            entity_confidence=entity_conf,
            segment_confidence=segment_conf,
            pattern_confidence=pattern_conf,
            error_count=self.metrics[video_id]['errors']
        )
        
        # Log metrics
        logger.info(f"Analysis completed for {video_id}:")
        logger.info(f"- Processing time: {elapsed:.2f}s")
        logger.info(f"- Entities found: {num_entities}")
        logger.info(f"- Segments identified: {num_segments}")
        logger.info(f"- Patterns detected: {num_patterns}")
        logger.info(f"- Average confidences: ")
        logger.info(f"  * Entities: {entity_conf:.2f}")
        logger.info(f"  * Segments: {segment_conf:.2f}")
        logger.info(f"  * Patterns: {pattern_conf:.2f}")
        
        return metrics