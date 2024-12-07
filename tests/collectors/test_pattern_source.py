"""Tests for pattern source management functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from gonzo.collectors.pattern_source import PatternSourceManager

@pytest.fixture
def mock_propaganda_transcript():
    """Sample transcript data for testing."""
    return [
        {
            "text": "And what we're seeing here is a classic manipulation tactic by mainstream media",
            "start": 0.0,
            "duration": 3.0
        },
        {
            "text": "where Jimmy Kimmel employs soft propaganda techniques to discredit RFK",
            "start": 3.0,
            "duration": 3.0
        },
        {
            "text": "rather than addressing the real health crisis in America.",
            "start": 6.0,
            "duration": 3.0
        },
        {
            "text": "This is a prime example of corporate media protecting big pharma interests.",
            "start": 9.0,
            "duration": 3.0
        }
    ]

@pytest.fixture
def mock_fear_transcript():
    """Sample transcript data for fear tactics."""
    return [
        {
            "text": "The deep state's primary tactic during the pandemic was fear manipulation",
            "start": 0.0,
            "duration": 3.0
        },
        {
            "text": "while pharmaceutical companies made unprecedented profits",
            "start": 3.0,
            "duration": 3.0
        },
        {
            "text": "from their experimental vaccines without proper long-term testing.",
            "start": 6.0,
            "duration": 3.0
        }
    ]

@pytest.fixture
def mock_economic_transcript():
    """Sample transcript data for economic manipulation."""
    return [
        {
            "text": "Legacy media continues to downplay the severity of inflation",
            "start": 0.0,
            "duration": 3.0
        },
        {
            "text": "calling it transitory while Americans struggle with rising costs",
            "start": 3.0,
            "duration": 3.0
        },
        {
            "text": "This manipulation of economic narrative protects corporate interests.",
            "start": 6.0,
            "duration": 3.0
        }
    ]

def test_extract_soft_propaganda_pattern(mock_propaganda_transcript):
    """Test detection of soft propaganda patterns in media."""
    manager = PatternSourceManager()
    
    with patch('gonzo.collectors.youtube.YouTubeCollector.get_video_transcript') as mock_get:
        mock_get.return_value = mock_propaganda_transcript
        patterns = manager.extract_patterns_from_video("https://youtube.com/watch?v=test")
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern["type"] == "manipulation_pattern"
        assert pattern["pattern_category"] == "soft_propaganda"
        assert "mainstream media" in pattern["description"].lower()

def test_extract_fear_tactics_pattern(mock_fear_transcript):
    """Test detection of fear manipulation patterns."""
    manager = PatternSourceManager()
    
    with patch('gonzo.collectors.youtube.YouTubeCollector.get_video_transcript') as mock_get:
        mock_get.return_value = mock_fear_transcript
        patterns = manager.extract_patterns_from_video("https://youtube.com/watch?v=test")
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern["pattern_category"] == "fear_tactics"
        assert "fear" in pattern["description"].lower()

def test_extract_economic_manipulation_pattern(mock_economic_transcript):
    """Test detection of economic narrative manipulation."""
    manager = PatternSourceManager()
    
    with patch('gonzo.collectors.youtube.YouTubeCollector.get_video_transcript') as mock_get:
        mock_get.return_value = mock_economic_transcript
        patterns = manager.extract_patterns_from_video("https://youtube.com/watch?v=test")
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern["pattern_category"] == "economic_manipulation"
        assert "inflation" in pattern["description"].lower()

def test_pattern_caching(mock_propaganda_transcript):
    """Test that patterns are properly cached."""
    manager = PatternSourceManager()
    
    with patch('gonzo.collectors.youtube.YouTubeCollector.get_video_transcript') as mock_get:
        mock_get.return_value = mock_propaganda_transcript
        video_url = "https://youtube.com/watch?v=test"
        
        # Extract patterns
        patterns = manager.extract_patterns_from_video(video_url)
        
        # Check cache
        cache = manager.get_cached_patterns()
        assert len(cache) > 0
        assert "test" in next(iter(cache.keys()))
        assert cache[next(iter(cache.keys()))]["patterns"] == patterns

def test_invalid_video_url():
    """Test handling of invalid video URL."""
    manager = PatternSourceManager()
    patterns = manager.extract_patterns_from_video("https://invalid-url.com")
    assert patterns == []

def test_empty_transcript():
    """Test handling of empty transcript."""
    manager = PatternSourceManager()
    
    with patch('gonzo.collectors.youtube.YouTubeCollector.get_video_transcript') as mock_get:
        mock_get.return_value = []
        patterns = manager.extract_patterns_from_video("https://youtube.com/watch?v=test")
        assert patterns == []