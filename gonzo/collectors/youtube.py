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
from ..config import ANALYSIS_CONFIG

logger = logging.getLogger(__name__)

class YouTubeCollector:
    """Collects and processes YouTube transcripts and metadata."""
    
    def __init__(self, agent=None, pattern_detector: Optional[PatternDetector] = None):
        """Initialize the collector.
        
        Args:
            agent: OpenAI agent for advanced processing
            pattern_detector: Pattern detector for analysis
        """
        self._transcript_api = YouTubeTranscriptApi
        self.agent = agent
        self.pattern_detector = pattern_detector
        self.task_manager = TaskManager(agent) if agent else None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ANALYSIS_CONFIG["chunk_size"],
            chunk_overlap=ANALYSIS_CONFIG["chunk_overlap"]
        )
    
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