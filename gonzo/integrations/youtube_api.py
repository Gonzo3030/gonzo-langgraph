from typing import Dict, List, Optional
from dataclasses import dataclass
from youtube_transcript_api import YouTubeTranscriptApi
from ..types import ContentSource, EntityType

@dataclass
class YouTubeMetadata:
    video_id: str
    title: Optional[str] = None
    channel: Optional[str] = None
    publish_date: Optional[str] = None

class YouTubeAPI(ContentSource):
    """YouTube API integration for Gonzo
    
    Handles fetching transcripts and metadata from YouTube videos.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube API client
        
        Args:
            api_key: Optional YouTube Data API key for metadata access
        """
        self.api_key = api_key
        self.transcript_api = YouTubeTranscriptApi()
    
    def get_transcript(self, video_id: str) -> List[Dict]:
        """Get transcript for a YouTube video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of transcript segments with timing information
        """
        try:
            transcript = self.transcript_api.get_transcript(video_id)
            return transcript
        except Exception as e:
            raise ValueError(f"Failed to fetch transcript for video {video_id}: {str(e)}")
    
    def get_metadata(self, video_id: str) -> YouTubeMetadata:
        """Get metadata for a YouTube video
        
        Requires API key to be set.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            YouTubeMetadata object
        """
        if not self.api_key:
            return YouTubeMetadata(video_id=video_id)
            
        # TODO: Implement metadata fetching using YouTube Data API
        return YouTubeMetadata(video_id=video_id)
