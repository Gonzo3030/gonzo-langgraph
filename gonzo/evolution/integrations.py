"""Integration utilities for the evolution system."""

from typing import Optional, Dict, Any
from pathlib import Path
from langchain_core.language_models import BaseLLM
from ..patterns.detector import PatternDetector
from ..collectors.youtube import YouTubeCollector
from .system import GonzoEvolutionSystem

class EvolutionIntegrator:
    """Handles integration of evolution system with other components."""
    
    @staticmethod
    def create_youtube_collector(
        llm: BaseLLM,
        pattern_detector: PatternDetector,
        youtube_api_key: Optional[str] = None,
        storage_path: Optional[Path] = None
    ) -> YouTubeCollector:
        """Create a YouTube collector with evolution system integration.
        
        Args:
            llm: Language model for analysis
            pattern_detector: Pattern detector instance
            youtube_api_key: Optional YouTube Data API key
            storage_path: Optional path for storing evolution data
            
        Returns:
            Configured YouTubeCollector instance
        """
        # Create evolution system
        evolution_system = GonzoEvolutionSystem(
            llm=llm,
            pattern_detector=pattern_detector,
            storage_path=storage_path
        )
        
        # Create and return collector
        return YouTubeCollector(
            agent=llm,
            pattern_detector=pattern_detector,
            youtube_api_key=youtube_api_key,
            evolution_system=evolution_system
        )
    
    @staticmethod
    async def process_historical_content(
        collector: YouTubeCollector,
        video_ids: list[str]
    ) -> Dict[str, Any]:
        """Process a set of historical videos to bootstrap evolution.
        
        Args:
            collector: Configured YouTubeCollector instance
            video_ids: List of video IDs to process
            
        Returns:
            Summary of processing results
        """
        results = {
            'processed': 0,
            'failed': 0,
            'evolution_metrics': None
        }
        
        for video_id in video_ids:
            try:
                # Analyze content
                analysis = await collector.analyze_content(video_id)
                
                if 'error' not in analysis:
                    results['processed'] += 1
                    
                    # Store latest evolution metrics
                    if 'evolution_metrics' in analysis:
                        results['evolution_metrics'] = analysis['evolution_metrics']
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                
        return results
