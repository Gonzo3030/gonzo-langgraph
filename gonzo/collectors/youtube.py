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
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
    def get_video_transcript(self, video_id: str) -> List[Dict[str, Any]]:
        """Get transcript for a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of transcript segments with timing
        """
        try:
            transcript = self._transcript_api.get_transcript(video_id)
            logger.info(f"Retrieved transcript for video {video_id}")
            return transcript
        except Exception as e:
            logger.error(f"Failed to get transcript for video {video_id}: {str(e)}")
            return []
            
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID if found, None otherwise
        """
        try:
            parsed = urlparse(url)
            if parsed.hostname == 'youtu.be':
                return parsed.path[1:]
            if parsed.hostname in ('www.youtube.com', 'youtube.com'):
                if parsed.path == '/watch':
                    return parse_qs(parsed.query)['v'][0]
                if parsed.path[:7] == '/embed/':
                    return parsed.path.split('/')[2]
                if parsed.path[:3] == '/v/':
                    return parsed.path.split('/')[2]
        except Exception as e:
            logger.error(f"Failed to extract video ID from URL {url}: {str(e)}")
            return None
        return None
        
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
            Dictionary of video IDs to transcripts
        """
        # TODO: Implement channel video listing and transcript collection
        # Will require YouTube API integration
        return {}
        
    def process_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """Process transcript into clean text.
        
        Args:
            transcript: Raw transcript data
            
        Returns:
            Cleaned transcript text
        """
        return " ".join([segment["text"] for segment in transcript])
    
    def extract_entities(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract entities from transcript using OpenAI agent.
        
        Args:
            transcript: Raw transcript data
            
        Returns:
            List of extracted entities with metadata
        """
        if not self.agent:
            logger.warning("No agent provided for entity extraction")
            return []
            
        # Process transcript into chunks
        text = self.process_transcript(transcript)
        chunks = self.text_splitter.split_text(text)
        
        entities = []
        for i, chunk in enumerate(chunks):
            # Use agent to extract entities
            # Provide chunk index for temporal ordering
            response = self.agent.run({
                "task": "entity_extraction",
                "text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "context": "YouTube transcript analysis"
            })
            
            # Process agent response into entities
            chunk_entities = self._process_agent_entities(response)
            entities.extend(chunk_entities)
            
        return entities
        
    def _process_agent_entities(self, agent_response: Dict[str, Any]) -> List[TimeAwareEntity]:
        """Process agent response into structured entities.
        
        Expected agent response format:
        {
            "entities": [
                {
                    "text": str,
                    "type": str,
                    "properties": Dict[str, Any],
                    "timestamp": float,
                    "confidence": float,
                    "relationships": List[Dict]
                },
                ...
            ]
        }
        
        Args:
            agent_response: Raw agent response
            
        Returns:
            List of processed entities
        """
        processed_entities = []
        
        try:
            now = datetime.now(UTC)
            
            for entity_data in agent_response.get("entities", []):
                # Create properties
                properties = {}
                for key, value in entity_data.get("properties", {}).items():
                    properties[key] = Property(
                        key=key,
                        value=value,
                        timestamp=now,
                        confidence=entity_data.get("confidence", 0.8)
                    )
                
                # Create entity
                entity = TimeAwareEntity(
                    id=uuid4(),
                    type=entity_data["type"],
                    properties=properties,
                    valid_from=now,
                    metadata={
                        "source": "youtube_transcript",
                        "original_text": entity_data["text"],
                        "timestamp": entity_data.get("timestamp"),
                    }
                )
                
                processed_entities.append(entity)
                
                # Process relationships if any
                for rel in entity_data.get("relationships", []):
                    relationship = Relationship(
                        id=uuid4(),
                        type=rel["type"],
                        source_id=entity.id,
                        target_id=rel["target_id"],
                        confidence=rel.get("confidence", 0.8),
                        properties={
                            k: Property(key=k, value=v)
                            for k, v in rel.get("properties", {}).items()
                        }
                    )
                    
                    # Add to entity metadata for pattern detection
                    if "relationships" not in entity.metadata:
                        entity.metadata["relationships"] = []
                    entity.metadata["relationships"].append(relationship)
                    
        except Exception as e:
            logger.error(f"Failed to process agent entities: {str(e)}")
            
        return processed_entities
        
    def segment_by_topic(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Segment transcript into topic-based chunks using OpenAI agent.
        
        Args:
            transcript: Raw transcript data
            
        Returns:
            List of topic segments with metadata
        """
        if not self.agent:
            logger.warning("No agent provided for topic segmentation")
            return []
            
        # Process transcript into manageable chunks
        text = self.process_transcript(transcript)
        chunks = self.text_splitter.split_text(text)
        
        segments = []
        for i, chunk in enumerate(chunks):
            # Use agent to identify topic boundaries and labels
            response = self.agent.run({
                "task": "topic_segmentation",
                "text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "context": "YouTube content analysis"
            })
            
            # Process agent response into segments
            chunk_segments = self._process_agent_segments(response)
            segments.extend(chunk_segments)
            
        return segments
    
    def _process_agent_segments(self, agent_response: Dict[str, Any]) -> List[TimeAwareEntity]:
        """Process agent response into topic segments.
        
        Expected agent response format:
        {
            "segments": [
                {
                    "text": str,
                    "topic": str,
                    "start_time": float,
                    "end_time": float,
                    "confidence": float,
                    "properties": Dict[str, Any],
                    "transitions": List[Dict]
                },
                ...
            ]
        }
        
        Args:
            agent_response: Raw agent response
            
        Returns:
            List of processed segments as entities
        """
        processed_segments = []
        
        try:
            now = datetime.now(UTC)
            
            for segment_data in agent_response.get("segments", []):
                # Create properties including topic info
                properties = {
                    "topic": Property(
                        key="topic",
                        value=segment_data["topic"],
                        timestamp=now,
                        confidence=segment_data.get("confidence", 0.8)
                    ),
                    "category": Property(
                        key="category",
                        value=segment_data.get("category", "general"),
                        timestamp=now,
                        confidence=segment_data.get("confidence", 0.8)
                    )
                }
                
                # Add any additional properties
                for key, value in segment_data.get("properties", {}).items():
                    properties[key] = Property(
                        key=key,
                        value=value,
                        timestamp=now,
                        confidence=segment_data.get("confidence", 0.8)
                    )
                
                # Create segment entity
                segment = TimeAwareEntity(
                    id=uuid4(),
                    type="topic",
                    properties=properties,
                    valid_from=now,
                    metadata={
                        "source": "youtube_transcript",
                        "text": segment_data["text"],
                        "start_time": segment_data["start_time"],
                        "end_time": segment_data["end_time"]
                    }
                )
                
                processed_segments.append(segment)
                
                # Process transitions if any
                for trans in segment_data.get("transitions", []):
                    transition = Relationship(
                        id=uuid4(),
                        type="topic_transition",
                        source_id=segment.id,
                        target_id=trans["target_id"],
                        confidence=trans.get("confidence", 0.8),
                        properties={
                            k: Property(key=k, value=v)
                            for k, v in trans.get("properties", {}).items()
                        }
                    )
                    
                    # Add to segment metadata
                    if "transitions" not in segment.metadata:
                        segment.metadata["transitions"] = []
                    segment.metadata["transitions"].append(transition)
                    
        except Exception as e:
            logger.error(f"Failed to process agent segments: {str(e)}")
            
        return processed_segments
    
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
            
            # Additional pattern detection can be added here
        
        return {
            "video_id": video_id,
            "entities": entities,
            "segments": segments,
            "patterns": patterns
        }