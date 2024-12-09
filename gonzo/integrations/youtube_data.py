"""YouTube Data API integration for fetching channel information."""

from typing import List, Dict, Optional, Generator
from datetime import datetime
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class YouTubeDataAPI:
    """Wrapper for YouTube Data API v3."""
    
    def __init__(self, api_key: str):
        """Initialize the API client.
        
        Args:
            api_key: YouTube Data API key
        """
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
    def get_channel_id(self, channel_url: str) -> Optional[str]:
        """Extract channel ID from URL.
        
        Args:
            channel_url: Channel URL or custom URL
            
        Returns:
            Channel ID if found
        """
        try:
            # Try direct channel ID first
            if '/channel/' in channel_url:
                return channel_url.split('/channel/')[-1].split('/')[0]
                
            # Try custom URL
            if '/c/' in channel_url or '/@' in channel_url:
                custom_name = channel_url.split('/')[-1]
                
                # Search for channel
                request = self.youtube.search().list(
                    part='id',
                    q=custom_name,
                    type='channel',
                    maxResults=1
                )
                response = request.execute()
                
                if response['items']:
                    return response['items'][0]['id']['channelId']
                    
        except Exception as e:
            logger.error(f"Failed to get channel ID: {str(e)}")
            
        return None
        
    def get_channel_videos(self,
        channel_id: str,
        max_results: Optional[int] = None,
        published_after: Optional[datetime] = None
    ) -> Generator[Dict, None, None]:
        """Get videos from a channel.
        
        Args:
            channel_id: Channel ID
            max_results: Maximum number of videos to retrieve
            published_after: Only get videos published after this date
            
        Yields:
            Video information dictionary
        """
        try:
            # Get channel's uploaded videos playlist
            channels_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channels_response['items']:
                return
                
            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from playlist
            num_videos = 0
            page_token = None
            
            while True:
                # Check if we've reached max_results
                if max_results and num_videos >= max_results:
                    break
                    
                # Get playlist items
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=50,  # Max allowed per request
                    pageToken=page_token
                )
                response = request.execute()
                
                for item in response['items']:
                    video = item['snippet']
                    
                    # Check publication date
                    if published_after:
                        video_date = datetime.strptime(
                            video['publishedAt'],
                            '%Y-%m-%dT%H:%M:%SZ'
                        )
                        if video_date < published_after:
                            continue
                    
                    yield {
                        'video_id': video['resourceId']['videoId'],
                        'title': video['title'],
                        'description': video['description'],
                        'published_at': video['publishedAt']
                    }
                    
                    num_videos += 1
                    if max_results and num_videos >= max_results:
                        break
                        
                # Check for next page
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as e:
            logger.error(f"YouTube API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to get channel videos: {str(e)}")