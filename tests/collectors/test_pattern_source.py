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
            "text": "Late night TV host Jimmy Kimmel uses his platform to mock RFK Jr's health advocacy",
            "start": 0.0,
            "duration": 3.0
        },
        {
            "text": "This coordinated media attack comes right after RFK's criticism of big pharma",
            "start": 3.0,
            "duration": 3.0
        },
        {
            "text": "Notice how they focus on personality rather than addressing the actual health crisis.",
            "start": 6.0,
            "duration": 3.0
        }
    ]

@pytest.fixture
def mock_fear_transcript():
    """Sample transcript data for fear tactics."""
    return [
        {
            "text": "The pandemic response relied heavily on fear tactics and emergency measures",
            "start": 0.0,
            "duration": 3.0
        },
        {
            "text": "creating unprecedented panic while pharmaceutical profits soared",
            "start": 3.0,
            "duration": 3.0
        },
        {
            "text": "experimental vaccines rushed through without proper safety trials.",
            "start": 6.0,
            "duration": 3.0
        }
    ]

@pytest.fixture
def mock_economic_transcript():
    """Sample transcript data for economic manipulation."""
    return [
        {
            "text": "While inflation reaches record highs and markets tumble",
            "start": 0.0,
            "duration": 3.0
        },
        {
            "text": "financial experts keep claiming economic indicators are healthy",
            "start": 3.0,
            "duration": 3.0
        },
        {
            "text": "as working families struggle with rising costs and falling wages.",
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
        assert "media" in pattern["description"].lower()

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
        assert any(term in pattern["description"].lower() 
                  for term in ["inflation", "economic", "financial"])

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