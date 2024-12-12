"""YouTube transcript and content collector with evolution system integration."""

from typing import List, Dict, Optional, Any
from datetime import datetime, UTC
from uuid import uuid4
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from urllib.parse import urlparse, parse_qs
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..types import EntityType, TimeAwareEntity, Property, Relationship
from ..patterns.detector import PatternDetector
from ..tasks.task_manager import TaskManager, TaskInput
from ..integrations.youtube_data import YouTubeDataAPI
from ..config import ANALYSIS_CONFIG
from ..evolution import GonzoEvolutionSystem

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler if not already present
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class YouTubeCollector:
    """Collects and processes YouTube transcripts and metadata."""
    
    def __init__(self, 
        agent=None, 
        pattern_detector: Optional[PatternDetector] = None,
        youtube_api_key: Optional[str] = None,
        evolution_system: Optional[GonzoEvolutionSystem] = None
    ):
        """Initialize the collector.
        
        Args:
            agent: OpenAI agent for advanced processing
            pattern_detector: Pattern detector for analysis
            youtube_api_key: Optional YouTube Data API key
            evolution_system: Optional evolution system for content learning
        """
        logger.debug(f"Initializing YouTubeCollector with API key present: {youtube_api_key is not None}")
        self._transcript_api = YouTubeTranscriptApi
        self.agent = agent
        self.pattern_detector = pattern_detector
        self.evolution_system = evolution_system
        self.task_manager = TaskManager(agent) if agent else None
        self.youtube_api = YouTubeDataAPI(youtube_api_key) if youtube_api_key else None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ANALYSIS_CONFIG["chunk_size"],
            chunk_overlap=ANALYSIS_CONFIG["chunk_overlap"]
        )

    async def analyze_content(self, video_id: str) -> Dict[str, Any]:
        """Full content analysis pipeline with evolution integration.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Analysis results including entities and patterns
        """
        # Get transcript
        transcript = self.get_video_transcript(video_id)
        if not transcript:
            logger.error(f"Could not get transcript for video {video_id}")
            return {
                "video_id": video_id,
                "entities": [],
                "segments": [],
                "patterns": [],
                "error": "No transcript available"
            }
        
        try:
            # Extract entities
            entities = self.extract_entities(transcript)
            
            # Segment by topic
            segments = self.segment_by_topic(transcript)
            
            # Detect patterns if available
            patterns = []
            if self.pattern_detector:
                # Get topic cycles from segments
                topic_patterns = self.pattern_detector.detect_topic_cycles()
                patterns.extend(topic_patterns)
            
            # Create analysis results
            analysis_results = {
                "video_id": video_id,
                "entities": entities,
                "segments": segments,
                "patterns": patterns
            }
            
            # Process through evolution system if available
            if self.evolution_system:
                try:
                    await self.evolution_system.process_youtube_content(analysis_results)
                    
                    # Get evolved analysis if available
                    evolved_analysis = await self.evolution_system.analyze_entities(entities)
                    
                    # Update patterns with evolved understanding
                    if 'patterns' in evolved_analysis:
                        analysis_results['patterns'] = evolved_analysis['patterns']
                    
                    # Add evolution metrics
                    if 'metrics' in evolved_analysis:
                        analysis_results['evolution_metrics'] = evolved_analysis['metrics']
                        
                except Exception as e:
                    logger.error(f"Evolution processing error for video {video_id}: {str(e)}")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing video {video_id}: {str(e)}")
            return {
                "video_id": video_id,
                "entities": [],
                "segments": [],
                "patterns": [],
                "error": str(e)
            }

    # ... [previous methods remain unchanged] ...
