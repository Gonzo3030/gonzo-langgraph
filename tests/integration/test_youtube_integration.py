"""Integration tests for YouTube content processing."""

import pytest
from unittest.mock import patch
from gonzo.collectors.youtube import YouTubeCollector
from gonzo.nodes.pattern_detection import detect_patterns

@pytest.mark.asyncio
async def test_youtube_transcript_processing(
    mock_transcript_data,
    mock_llm,
    base_state,
    evolution_system
):
    """Test processing of YouTube transcripts"""
    collector = YouTubeCollector(
        agent=mock_llm,
        evolution_system=evolution_system
    )
    
    # Mock transcript API call
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript', return_value=mock_transcript_data):
        # Get and process transcript
        transcript = collector.get_video_transcript('test_video')
        assert transcript == mock_transcript_data
        
        # Process transcript and update state
        processed_text = collector.process_transcript(transcript)
        base_state.messages.current_message = processed_text
        
        # Verify transcript processing
        assert '[0s]' in processed_text
        assert 'manipulation' in processed_text
        assert 'San Francisco' in processed_text

@pytest.mark.asyncio
async def test_entity_extraction(
    mock_transcript_data,
    mock_llm,
    base_state,
    evolution_system
):
    """Test entity extraction from transcripts"""
    collector = YouTubeCollector(
        agent=mock_llm,
        evolution_system=evolution_system
    )
    
    # Process transcript and extract entities
    processed_text = collector.process_transcript(mock_transcript_data)
    base_state.messages.current_message = processed_text
    
    # Extract entities and update state
    entities = await collector.extract_entities(base_state)
    base_state.analysis.entities = entities
    
    # Verify entity extraction
    assert isinstance(entities, list)
    assert any(entity.get('text') == 'San Francisco' for entity in entities)

@pytest.mark.asyncio
async def test_full_content_analysis(
    mock_transcript_data,
    mock_video_data,
    mock_llm,
    base_state,
    evolution_system
):
    """Test complete content analysis pipeline"""
    collector = YouTubeCollector(
        agent=mock_llm,
        evolution_system=evolution_system
    )
    
    # Mock transcript and perform analysis
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript', return_value=mock_transcript_data):
        # Process content and update state
        processed_text = collector.process_transcript(mock_transcript_data)
        base_state.messages.current_message = processed_text
        
        # Extract entities
        entities = await collector.extract_entities(base_state)
        base_state.analysis.entities = entities
        
        # Detect patterns
        result = await detect_patterns(base_state, mock_llm)
        updated_state = result['state']
        
        # Verify results
        assert len(updated_state.analysis.patterns) > 0
        assert updated_state.analysis.significance > 0
        assert any('manipulation' in pattern['content'] for pattern in updated_state.analysis.patterns)

@pytest.mark.asyncio
async def test_channel_collection(
    mock_video_data,
    mock_llm,
    base_state,
    evolution_system,
    mock_transcript_data
):
    """Test channel-wide content collection"""
    collector = YouTubeCollector(
        agent=mock_llm,
        evolution_system=evolution_system,
        youtube_api_key='test_key'
    )
    
    # Mock API calls
    with patch('gonzo.integrations.youtube_data.YouTubeDataAPI.get_channel_videos',
              return_value=[mock_video_data]):
        with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript',
                  return_value=mock_transcript_data):
            # Collect channel transcripts
            transcripts = await collector.collect_channel_transcripts(
                base_state,
                channel_url='https://youtube.com/test',
                max_videos=1
            )
            
            # Verify collection results
            assert len(transcripts) > 0
            assert 'test_video' in transcripts
            assert 'transcript' in transcripts['test_video']
            assert 'metadata' in transcripts['test_video']

@pytest.mark.asyncio
async def test_evolution_integration(
    mock_transcript_data,
    mock_llm,
    base_state,
    evolution_system
):
    """Test integration with evolution system"""
    collector = YouTubeCollector(
        agent=mock_llm,
        evolution_system=evolution_system
    )
    
    # Process content and update state
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript', return_value=mock_transcript_data):
        processed_text = collector.process_transcript(mock_transcript_data)
        base_state.messages.current_message = processed_text
        
        # Extract entities and detect patterns
        entities = await collector.extract_entities(base_state)
        base_state.analysis.entities = entities
        
        result = await detect_patterns(base_state, mock_llm)
        updated_state = result['state']
        
        # Update evolution metrics
        await evolution_system.update_metrics(updated_state)
        
        # Verify evolution integration
        metrics = await evolution_system.get_current_metrics()
        assert metrics is not None
        assert 'pattern_confidence' in metrics
        assert len(updated_state.analysis.patterns) > 0
