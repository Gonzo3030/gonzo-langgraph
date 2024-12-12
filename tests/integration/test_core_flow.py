import pytest
from pathlib import Path
import asyncio
from datetime import datetime, UTC
from langchain_core.language_models import BaseLLM
from gonzo.collectors.youtube import YouTubeCollector
from gonzo.patterns.detector import PatternDetector
from gonzo.evolution import GonzoEvolutionSystem
from gonzo.prompts.dynamic import DynamicPromptSystem
from gonzo.response.types import ResponseType, ResponseTypeManager
from gonzo.interaction.state import InteractionStateManager
from gonzo.context.time_periods import TimePeriodManager

class MockLLM(BaseLLM):
    """Mock LLM for testing"""
    def invoke(self, prompt):
        return "This is a test response from Gonzo."

@pytest.fixture
def test_storage_path(tmp_path):
    return tmp_path / "test_storage"

@pytest.fixture
def mock_llm():
    return MockLLM()

@pytest.fixture
def pattern_detector():
    return PatternDetector()

@pytest.fixture
def evolution_system(mock_llm, pattern_detector, test_storage_path):
    return GonzoEvolutionSystem(
        llm=mock_llm,
        pattern_detector=pattern_detector,
        storage_path=test_storage_path
    )

@pytest.fixture
def youtube_collector(mock_llm, pattern_detector, evolution_system):
    return YouTubeCollector(
        agent=mock_llm,
        pattern_detector=pattern_detector,
        evolution_system=evolution_system
    )

@pytest.fixture
def prompt_system():
    return DynamicPromptSystem()

@pytest.fixture
def response_manager():
    return ResponseTypeManager()

@pytest.fixture
def interaction_manager():
    return InteractionStateManager()

@pytest.fixture
def time_period_manager():
    return TimePeriodManager()

@pytest.mark.asyncio
async def test_youtube_content_processing(
    youtube_collector,
    evolution_system,
    prompt_system,
    response_manager,
    interaction_manager,
    time_period_manager
):
    """Test full processing of YouTube content"""
    # Mock YouTube content
    mock_content = {
        'video_id': 'test_video',
        'text': 'Test video about AI and corporate control',
        'entities': [],
        'patterns': [{
            'type': 'manipulation',
            'confidence': 0.8,
            'description': 'Corporate control pattern'
        }]
    }
    
    # Process through evolution system
    await evolution_system.process_youtube_content(mock_content)
    
    # Get current metrics
    metrics = await evolution_system.get_current_metrics()
    assert metrics is not None
    
    # Generate response
    response_type = response_manager.select_response_type(mock_content, metrics.__dict__)
    assert response_type in ResponseType
    
    # Build prompt
    prompt = prompt_system.build_prompt(
        response_type=response_type,
        content=mock_content,
        evolution_metrics=metrics.__dict__,
        time_period_manager=time_period_manager
    )
    assert prompt is not None

@pytest.mark.asyncio
async def test_interaction_flow(
    interaction_manager,
    prompt_system,
    response_manager,
    time_period_manager
):
    """Test interaction flow for X conversations"""
    # Start conversation
    initial_tweet = {
        'text': 'What do you think about the latest AI developments?',
        'user_id': 'test_user',
        'hashtags': ['AI', 'Technology']
    }
    
    context = await interaction_manager.start_conversation(
        thread_id='test_thread',
        initial_tweet=initial_tweet,
        participants=['test_user']
    )
    assert context is not None
    
    # Update conversation
    updated_context = await interaction_manager.update_conversation(
        thread_id='test_thread',
        new_tweet={
            'text': 'Interesting perspective on AI control',
            'user_id': 'test_user'
        },
        response_type='quick_take'
    )
    assert updated_context is not None
    assert len(updated_context.topics) > 0

@pytest.mark.asyncio
async def test_temporal_connections(
    evolution_system,
    time_period_manager,
    prompt_system
):
    """Test historical connections and time period analysis"""
    # Mock content with temporal relevance
    mock_content = {
        'text': 'Modern media manipulation through social networks',
        'patterns': [{
            'type': 'manipulation',
            'temporal_key': 'media_control',
            'confidence': 0.9
        }]
    }
    
    # Analyze temporal connections
    connections = time_period_manager.analyze_temporal_connections(
        mock_content,
        {'pattern_confidence': 0.8}
    )
    assert len(connections) > 0
    
    # Get historical context
    context = time_period_manager.build_historical_context(connections)
    assert context is not None

@pytest.mark.asyncio
async def test_end_to_end_flow(
    youtube_collector,
    evolution_system,
    prompt_system,
    response_manager,
    interaction_manager,
    time_period_manager
):
    """Test complete end-to-end flow"""
    # Process content
    mock_content = {
        'video_id': 'test_video',
        'text': 'Test video about corporate control and AI',
        'entities': [],
        'patterns': [{
            'type': 'manipulation',
            'confidence': 0.8
        }]
    }
    
    # Evolution processing
    await evolution_system.process_youtube_content(mock_content)
    metrics = await evolution_system.get_current_metrics()
    
    # Response generation
    response_type = response_manager.select_response_type(mock_content, metrics.__dict__)
    prompt = prompt_system.build_prompt(
        response_type=response_type,
        content=mock_content,
        evolution_metrics=metrics.__dict__,
        time_period_manager=time_period_manager
    )
    
    # Start conversation
    context = await interaction_manager.start_conversation(
        thread_id='test_thread',
        initial_tweet=mock_content,
        participants=['test_user']
    )
    
    # Verify entire flow
    assert metrics is not None
    assert response_type in ResponseType
    assert prompt is not None
    assert context is not None
