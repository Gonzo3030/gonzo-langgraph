import pytest
from pathlib import Path
import asyncio
from datetime import datetime, UTC
from unittest.mock import MagicMock, patch
from gonzo.collectors.youtube import YouTubeCollector
from gonzo.evolution import GonzoEvolutionSystem
from gonzo.patterns.detector import PatternDetector

@pytest.fixture
def mock_transcript_data():
    return [
        {
            'text': 'This is a test transcript about corporate control',
            'start': 0.0,
            'duration': 2.0
        },
        {
            'text': 'And the manipulation of digital reality',
            'start': 2.0,
            'duration': 2.0
        }
    ]

@pytest.fixture
def mock_video_data():
    return {
        'video_id': 'test_video',
        'title': 'Test Video',
        'description': 'A test video about corporate control',
        'published_at': '2024-01-01T00:00:00Z'
    }

@pytest.mark.asyncio
async def test_youtube_transcript_processing(
    mock_transcript_data,
    mock_llm,
    pattern_detector,
    evolution_system
):
    """Test processing of YouTube transcripts"""
    collector = YouTubeCollector(
        agent=mock_llm,
        pattern_detector=pattern_detector,
        evolution_system=evolution_system
    )
    
    # Mock transcript API call
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript', return_value=mock_transcript_data):
        transcript = collector.get_video_transcript('test_video')
        assert transcript == mock_transcript_data
        
        # Test transcript processing
        processed_text = collector.process_transcript(transcript)
        assert '[0s]' in processed_text
        assert 'corporate control' in processed_text

@pytest.mark.asyncio
async def test_entity_extraction(
    mock_transcript_data,
    mock_llm,
    pattern_detector,
    evolution_system
):
    """Test entity extraction from transcripts"""
    collector = YouTubeCollector(
        agent=mock_llm,
        pattern_detector=pattern_detector,
        evolution_system=evolution_system
    )
    
    # Test entity extraction
    entities = collector.extract_entities(mock_transcript_data)
    assert isinstance(entities, list)

@pytest.mark.asyncio
async def test_full_content_analysis(
    mock_transcript_data,
    mock_video_data,
    mock_llm,
    pattern_detector,
    evolution_system
):
    """Test complete content analysis pipeline"""
    collector = YouTubeCollector(
        agent=mock_llm,
        pattern_detector=pattern_detector,
        evolution_system=evolution_system
    )
    
    # Mock transcript and analysis
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript', return_value=mock_transcript_data):
        analysis_results = await collector.analyze_content('test_video')
        
        assert 'video_id' in analysis_results
        assert 'entities' in analysis_results
        assert 'segments' in analysis_results
        assert 'patterns' in analysis_results
        assert 'error' not in analysis_results

@pytest.mark.asyncio
async def test_channel_collection(
    mock_video_data,
    mock_llm,
    pattern_detector,
    evolution_system
):
    """Test channel-wide content collection"""
    collector = YouTubeCollector(
        agent=mock_llm,
        pattern_detector=pattern_detector,
        evolution_system=evolution_system,
        youtube_api_key='test_key'
    )
    
    # Mock YouTube Data API
    with patch('gonzo.integrations.youtube_data.YouTubeDataAPI.get_channel_videos',
              return_value=[mock_video_data]):
        with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript',
                  return_value=mock_transcript_data):
            transcripts = collector.collect_channel_transcripts(
                channel_url='https://youtube.com/test',
                max_videos=1
            )
            
            assert len(transcripts) > 0
            assert 'test_video' in transcripts
            assert 'transcript' in transcripts['test_video']
            assert 'metadata' in transcripts['test_video']

@pytest.mark.asyncio
async def test_evolution_integration(
    mock_transcript_data,
    mock_llm,
    pattern_detector,
    evolution_system
):
    """Test integration with evolution system"""
    collector = YouTubeCollector(
        agent=mock_llm,
        pattern_detector=pattern_detector,
        evolution_system=evolution_system
    )
    
    # Mock transcript and analysis
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript', return_value=mock_transcript_data):
        analysis_results = await collector.analyze_content('test_video')
        
        # Verify evolution processing
        metrics = await evolution_system.get_current_metrics()
        assert metrics is not None
        
        # Verify pattern detection integration
        assert len(analysis_results['patterns']) >= 0
        
        # Verify evolution metrics in results
        if 'evolution_metrics' in analysis_results:
            assert 'pattern_confidence' in analysis_results['evolution_metrics']
