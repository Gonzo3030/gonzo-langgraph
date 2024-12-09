"""YouTube transcript and content collector."""

from typing import List, Dict, Optional, Any
from datetime import datetime, UTC
from uuid import uuid4
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..types import EntityType, TimeAwareEntity, Property, Relationship
from ..patterns.detector import PatternDetector
from ..tasks.task_manager import TaskManager, TaskInput
from ..integrations.youtube_data import YouTubeDataAPI
from ..config import ANALYSIS_CONFIG

logger = logging.getLogger(__name__)

class YouTubeCollector:
    """Collects and processes YouTube transcripts and metadata."""
    
    def __init__(self, 
        agent=None, 
        pattern_detector: Optional[PatternDetector] = None,
        youtube_api_key: Optional[str] = None
    ):
        """Initialize the collector.
        
        Args:
            agent: OpenAI agent for advanced processing
            pattern_detector: Pattern detector for analysis
            youtube_api_key: Optional YouTube Data API key
        """
        self._transcript_api = YouTubeTranscriptApi
        self.agent = agent
        self.pattern_detector = pattern_detector
        self.task_manager = TaskManager(agent) if agent else None
        self.youtube_api = YouTubeDataAPI(youtube_api_key) if youtube_api_key else None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ANALYSIS_CONFIG["chunk_size"],
            chunk_overlap=ANALYSIS_CONFIG["chunk_overlap"]
        )
    
    def collect_channel_transcripts(self, 
        channel_url: str,
        max_videos: Optional[int] = None,
        from_date: Optional[datetime] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Collect transcripts from a YouTube channel.
        
        Args:
            channel_url: Channel URL
            max_videos: Maximum number of videos to process
            from_date: Only collect videos after this date
            
        Returns:
            Dictionary of video IDs to transcripts with metadata
        """
        if not self.youtube_api:
            logger.error("YouTube Data API key required for channel collection")
            return {}
        
        try:
            # Get channel ID
            channel_id = self.youtube_api.get_channel_id(channel_url)
            if not channel_id:
                logger.error(f"Could not find channel ID for {channel_url}")
                return {}
            
            # Collect video transcripts
            transcripts = {}
            
            for video in self.youtube_api.get_channel_videos(
                channel_id=channel_id,
                max_results=max_videos,
                published_after=from_date
            ):
                video_id = video['video_id']
                
                # Get transcript
                transcript = self.get_video_transcript(video_id)
                if not transcript:
                    continue
                
                # Add video metadata
                transcripts[video_id] = {
                    'transcript': transcript,
                    'metadata': {
                        'title': video['title'],
                        'description': video['description'],
                        'published_at': video['published_at']
                    }
                }
                
            return transcripts
            
        except Exception as e:
            logger.error(f"Failed to collect channel transcripts: {str(e)}")
            return {}
    
    def extract_entities(self, transcript: List[Dict[str, Any]]) -> List[TimeAwareEntity]:
        """Extract entities from transcript using OpenAI agent.
        
        Args:
            transcript: Raw transcript data
            
        Returns:
            List of extracted entities
        """
        if not self.task_manager:
            logger.warning("No task manager available for entity extraction")
            return []
            
        # Process transcript into chunks
        text = self.process_transcript(transcript)
        chunks = self.text_splitter.split_text(text)
        
        entities = []
        for i, chunk in enumerate(chunks):
            # Prepare task input
            task_input = TaskInput(
                task="entity_extraction",
                text=chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                context="YouTube transcript analysis",
                metadata={"video_transcript": True}
            )
            
            # Execute task
            result = self.task_manager.execute_task(task_input)
            
            # Process entities
            if "entities" in result:
                chunk_entities = self._process_agent_entities(result)
                entities.extend(chunk_entities)
            
        return entities
    
    def segment_by_topic(self, transcript: List[Dict[str, Any]]) -> List[TimeAwareEntity]:
        """Segment transcript into topics using OpenAI agent.
        
        Args:
            transcript: Raw transcript data
            
        Returns:
            List of topic segments as entities
        """
        if not self.task_manager:
            logger.warning("No task manager available for topic segmentation")
            return []
            
        # Process transcript into chunks
        text = self.process_transcript(transcript)
        chunks = self.text_splitter.split_text(text)
        
        segments = []
        for i, chunk in enumerate(chunks):
            # Prepare task input
            task_input = TaskInput(
                task="topic_segmentation",
                text=chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                context="YouTube content analysis",
                metadata={"video_transcript": True}
            )
            
            # Execute task
            result = self.task_manager.execute_task(task_input)
            
            # Process segments
            if "segments" in result:
                chunk_segments = self._process_agent_segments(result)
                segments.extend(chunk_segments)
            
        return segments
    
    def analyze_content(self, video_id: str) -> Dict[str, Any]:
        """Full content analysis pipeline.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Analysis results including entities and patterns
        """
        # Get transcript
        transcript = self.get_video_transcript(video_id)
        if not transcript:
            return {}
        
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
        
        return {
            "video_id": video_id,
            "entities": entities,
            "segments": segments,
            "patterns": patterns
        }