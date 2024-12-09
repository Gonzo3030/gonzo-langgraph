import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from gonzo.integrations.youtube_data import YouTubeDataAPI

# Test data
SAMPLE_CHANNEL_URL = "https://www.youtube.com/channel/UC1234567890"
SAMPLE_CUSTOM_URL = "https://www.youtube.com/@TestChannel"
SAMPLE_CHANNEL_ID = "UC1234567890"

@pytest.fixture
def mock_youtube_service():
    """Create a mock YouTube service."""
    mock_service = Mock()
    
    # Mock channels list
    mock_channels = Mock()
    mock_channels.list.return_value.execute.return_value = {
        'items': [{
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': 'UU1234567890'
                }
            }
        }]
    }
    mock_service.channels = lambda: mock_channels
    
    # Mock playlist items list
    mock_playlist = Mock()
    mock_playlist.list.return_value.execute.return_value = {
        'items': [
            {
                'snippet': {
                    'resourceId': {'videoId': 'video123'},
                    'title': 'Test Video',
                    'description': 'Test Description',
                    'publishedAt': '2024-01-01T00:00:00Z'
                }
            }
        ]
    }
    mock_service.playlistItems = lambda: mock_playlist
    
    # Mock search
    mock_search = Mock()
    mock_search.list.return_value.execute.return_value = {
        'items': [{
            'id': {'channelId': SAMPLE_CHANNEL_ID}
        }]
    }
    mock_service.search = lambda: mock_search
    
    return mock_service

def test_init():
    """Test YouTubeDataAPI initialization."""
    api = YouTubeDataAPI("test_api_key")
    assert api is not None

@patch('googleapiclient.discovery.build')
def test_get_channel_id_from_channel_url(mock_build, mock_youtube_service):
    """Test getting channel ID from channel URL."""
    mock_build.return_value = mock_youtube_service
    api = YouTubeDataAPI("test_api_key")
    
    channel_id = api.get_channel_id(SAMPLE_CHANNEL_URL)
    assert channel_id == SAMPLE_CHANNEL_ID

@patch('googleapiclient.discovery.build')
def test_get_channel_id_from_custom_url(mock_build, mock_youtube_service):
    """Test getting channel ID from custom URL."""
    mock_build.return_value = mock_youtube_service
    api = YouTubeDataAPI("test_api_key")
    
    channel_id = api.get_channel_id(SAMPLE_CUSTOM_URL)
    assert channel_id == SAMPLE_CHANNEL_ID
    
@patch('googleapiclient.discovery.build')
def test_get_channel_videos(mock_build, mock_youtube_service):
    """Test getting videos from a channel."""
    mock_build.return_value = mock_youtube_service
    api = YouTubeDataAPI("test_api_key")
    
    videos = list(api.get_channel_videos(
        channel_id=SAMPLE_CHANNEL_ID,
        max_results=1
    ))
    
    assert len(videos) == 1
    assert videos[0]['video_id'] == 'video123'
    assert videos[0]['title'] == 'Test Video'

@patch('googleapiclient.discovery.build')
def test_get_channel_videos_with_date_filter(mock_build, mock_youtube_service):
    """Test getting videos with date filter."""
    mock_build.return_value = mock_youtube_service
    api = YouTubeDataAPI("test_api_key")
    
    # Test with date after video
    future_date = datetime(2024, 2, 1)
    videos = list(api.get_channel_videos(
        channel_id=SAMPLE_CHANNEL_ID,
        published_after=future_date
    ))
    assert len(videos) == 0
    
    # Test with date before video
    past_date = datetime(2023, 12, 1)
    videos = list(api.get_channel_videos(
        channel_id=SAMPLE_CHANNEL_ID,
        published_after=past_date
    ))
    assert len(videos) == 1

@patch('googleapiclient.discovery.build')
def test_error_handling(mock_build, mock_youtube_service):
    """Test error handling."""
    mock_build.return_value = mock_youtube_service
    api = YouTubeDataAPI("test_api_key")
    
    # Test invalid channel URL
    channel_id = api.get_channel_id("invalid_url")
    assert channel_id is None
    
    # Test empty channel response
    mock_youtube_service.channels().list.return_value.execute.return_value = {'items': []}
    videos = list(api.get_channel_videos(SAMPLE_CHANNEL_ID))
    assert len(videos) == 0
