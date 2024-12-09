"""YouTube transcript and content collector."""

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
        youtube_api_key: Optional[str] = None
    ):
        """Initialize the collector.
        
        Args:
            agent: OpenAI agent for advanced processing
            pattern_detector: Pattern detector for analysis
            youtube_api_key: Optional YouTube Data API key
        """
        logger.debug(f"Initializing YouTubeCollector with API key present: {youtube_api_key is not None}")
        self._transcript_api = YouTubeTranscriptApi
        self.agent = agent
        self.pattern_detector = pattern_detector
        self.task_manager = TaskManager(agent) if agent else None
        self.youtube_api = YouTubeDataAPI(youtube_api_key) if youtube_api_key else None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ANALYSIS_CONFIG["chunk_size"],
            chunk_overlap=ANALYSIS_CONFIG["chunk_overlap"]
        )

    def get_video_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of transcript segments or None if unavailable
        """
        logger.debug(f"Attempting to get transcript for video {video_id}")
        try:
            # First try direct transcript retrieval
            try:
                logger.debug("Attempting direct transcript retrieval")
                return self._transcript_api.get_transcript(video_id)
            except Exception as e:
                logger.debug(f"Direct retrieval failed: {str(e)}")
                
            # Try list_transcripts approach
            logger.debug("Attempting list_transcripts approach")
            transcript_list = self._transcript_api.list_transcripts(video_id)
            
            # Try to get English transcript first
            try:
                logger.debug("Looking for English transcript")
                transcript = transcript_list.find_transcript(['en'])
            except NoTranscriptFound:
                # Fallback to auto-generated English
                try:
                    logger.debug("Looking for auto-generated English transcript")
                    transcript = transcript_list.find_generated_transcript(['en'])
                except NoTranscriptFound:
                    # Final fallback - get first available and translate
                    logger.debug("Looking for any transcript to translate")
                    transcript = transcript_list.find_manually_created_transcript()
                    transcript = transcript.translate('en')
            
            result = transcript.fetch()
            logger.debug(f"Successfully retrieved transcript with {len(result)} segments")
            return result
            
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            logger.warning(f"No transcript available for video {video_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting transcript for video {video_id}: {str(e)}")
            return None

    def process_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """Process raw transcript into clean text.
        
        Args:
            transcript: Raw transcript data
            
        Returns:
            Processed text
        """
        # Combine transcript segments with timestamps
        text_segments = []
        for segment in transcript:
            start_time = segment['start']
            duration = segment.get('duration', 0)
            text = segment['text']
            
            # Add timestamp and segment
            timestamp = f"[{int(start_time)}s]"
            text_segments.append(f"{timestamp} {text}")
            
        return "\n".join(text_segments)
    
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
            
        if not transcript:
            logger.warning("No transcript provided for entity extraction")
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

    def _process_agent_entities(self, result: Dict[str, Any]) -> List[TimeAwareEntity]:
        """Process entities from agent result."""
        entities = []
        if "entities" in result:
            for entity_data in result["entities"]:
                entity = TimeAwareEntity(
                    type=entity_data.get("type", EntityType.UNKNOWN),
                    id=uuid4(),
                    properties={
                        "text": Property(key="text", value=entity_data.get("text", "")),
                        "confidence": Property(key="confidence", value=entity_data.get("confidence", 0.0))
                    },
                    valid_from=datetime.now(UTC)
                )
                entities.append(entity)
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

        if not transcript:
            logger.warning("No transcript provided for topic segmentation")
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

    def _process_agent_segments(self, result: Dict[str, Any]) -> List[TimeAwareEntity]:
        """Process segments from agent result."""
        segments = []
        if "segments" in result:
            for segment_data in result["segments"]:
                segment = TimeAwareEntity(
                    type=EntityType.NARRATIVE,
                    id=uuid4(),
                    properties={
                        "topic": Property(key="topic", value=segment_data.get("topic", "")),
                        "category": Property(key="category", value=segment_data.get("category", "")),
                        "start_time": Property(key="start_time", value=segment_data.get("start_time", 0))
                    },
                    valid_from=datetime.now(UTC)
                )
                segments.append(segment)
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
            
            return {
                "video_id": video_id,
                "entities": entities,
                "segments": segments,
                "patterns": patterns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing video {video_id}: {str(e)}")
            return {
                "video_id": video_id,
                "entities": [],
                "segments": [],
                "patterns": [],
                "error": str(e)
            }