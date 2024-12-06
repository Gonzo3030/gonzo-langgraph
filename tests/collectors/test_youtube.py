"""Tests for YouTube collector functionality."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from gonzo.collectors.youtube import YouTubeCollector

def test_extract_video_id_standard_url():
    """Test extracting video ID from standard YouTube URL."""
    collector = YouTubeCollector()
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    video_id = collector.extract_video_id(url)
    assert video_id == "dQw4w9WgXcQ"
    
def test_extract_video_id_short_url():
    """Test extracting video ID from youtu.be URL."""
    collector = YouTubeCollector()
    url = "https://youtu.be/dQw4w9WgXcQ"
    
    video_id = collector.extract_video_id(url)
    assert video_id == "dQw4w9WgXcQ"
    
def test_extract_video_id_embed_url():
    """Test extracting video ID from embed URL."""
    collector = YouTubeCollector()
    url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    
    video_id = collector.extract_video_id(url)
    assert video_id == "dQw4w9WgXcQ"
    
def test_extract_video_id_invalid_url():
    """Test handling invalid URL."""
    collector = YouTubeCollector()
    url = "https://example.com/video"
    
    video_id = collector.extract_video_id(url)
    assert video_id is None
    
@patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript')
def test_get_video_transcript(mock_get_transcript):
    """Test getting video transcript."""
    # Mock transcript data
    mock_transcript = [
        {
            "text": "First segment",
            "start": 0.0,
            "duration": 2.0
        },
        {
            "text": "Second segment",
            "start": 2.0,
            "duration": 2.0
        }
    ]
    mock_get_transcript.return_value = mock_transcript
    
    collector = YouTubeCollector()
    transcript = collector.get_video_transcript("test_video_id")
    
    assert transcript == mock_transcript
    mock_get_transcript.assert_called_once_with("test_video_id")
    
@patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript')
def test_get_video_transcript_error(mock_get_transcript):
    """Test handling transcript retrieval error."""
    mock_get_transcript.side_effect = Exception("API Error")
    
    collector = YouTubeCollector()
    transcript = collector.get_video_transcript("test_video_id")
    
    assert transcript == []
    
def test_process_transcript():
    """Test processing raw transcript into clean text."""
    collector = YouTubeCollector()
    transcript = [
        {"text": "First segment", "start": 0.0, "duration": 2.0},
        {"text": "Second segment", "start": 2.0, "duration": 2.0}
    ]
    
    text = collector.process_transcript(transcript)
    assert text == "First segment Second segment"