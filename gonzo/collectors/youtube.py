"""YouTube transcript and content collector."""

from typing import List, Dict, Optional, Any
from datetime import datetime, UTC
from uuid import uuid4
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from urllib.parse import urlparse, parse_qs
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..types import GonzoState
from ..evolution import GonzoEvolutionSystem
from ..config import ANALYSIS_CONFIG

logger = logging.getLogger(__name__)

class YouTubeCollector:
    """Collects and processes YouTube transcripts and metadata."""
    
    def __init__(self, 
        agent: Any,
        evolution_system: Optional[GonzoEvolutionSystem] = None,
        youtube_api_key: Optional[str] = None
    ):
        """Initialize collector.
        
        Args:
            agent: LLM agent for analysis
            evolution_system: Optional evolution system
            youtube_api_key: Optional YouTube Data API key
        """
        self.agent = agent
        self.evolution_system = evolution_system
        self._transcript_api = YouTubeTranscriptApi
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ANALYSIS_CONFIG["chunk_size"],
            chunk_overlap=ANALYSIS_CONFIG["chunk_overlap"]
        )

    async def analyze_content(self, video_id: str) -> Dict[str, Any]:
        """Analyze YouTube content.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Analysis results
        """
        # Get transcript
        transcript = self.get_video_transcript(video_id)
        if not transcript:
            return {"error": "No transcript available"}
            
        try:
            # Process transcript
            text = self.process_transcript(transcript)
            
            # Create state for analysis
            state = GonzoState()
            state.messages.current_message = text
            
            # Process through evolution system if available
            if self.evolution_system:
                await self.evolution_system.process_youtube_content({
                    "video_id": video_id,
                    "text": text
                })
                
                # Get metrics
                metrics = await self.evolution_system.get_current_metrics()
                
                return {
                    "video_id": video_id,
                    "text": text,
                    "evolution_metrics": metrics.__dict__ if metrics else None
                }
                
            return {
                "video_id": video_id,
                "text": text
            }
            
        except Exception as e:
            logger.error(f"Error analyzing video {video_id}: {str(e)}")
            return {"error": str(e)}
            
    def get_video_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get transcript for a video."""
        try:
            return self._transcript_api.get_transcript(video_id)
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return None
            
    def process_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """Process transcript into text."""
        text_segments = []
        for segment in transcript:
            timestamp = f"[{int(segment['start'])}s]"
            text_segments.append(f"{timestamp} {segment['text']}")
        return "\n".join(text_segments)