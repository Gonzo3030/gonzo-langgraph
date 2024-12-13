"""Test configuration and fixtures."""

import pytest
from pathlib import Path
from datetime import datetime
from .mocks.llm import MockLLM
from gonzo.evolution import GonzoEvolutionSystem
from gonzo.state import GonzoState, MessageState, AnalysisState, EvolutionState, InteractionState, ResponseState

@pytest.fixture
def mock_llm():
    """Provide mock language model."""
    return MockLLM()

@pytest.fixture
def test_storage_path(tmp_path):
    """Provide test storage path."""
    return tmp_path / "test_storage"

@pytest.fixture
def evolution_system(mock_llm, test_storage_path):
    """Provide evolution system."""
    return GonzoEvolutionSystem(
        llm=mock_llm,
        storage_path=test_storage_path
    )

@pytest.fixture
def base_state():
    """Provide base Gonzo state for testing."""
    return GonzoState(
        messages=MessageState(messages=[], current_message=None),
        analysis=AnalysisState(patterns=[], entities=[], significance=0.0),
        evolution=EvolutionState(
            pattern_confidence=0.5,
            narrative_consistency=0.5,
            prediction_accuracy=0.5,
            processed_content_ids=[]
        ),
        interaction=InteractionState(),
        response=ResponseState()
    )

@pytest.fixture
def mock_transcript_data():
    """Provide mock transcript data."""
    return [
        {
            'text': 'This manipulation reminds me of San Francisco in \'71, pure madness.',
            'start': 0.0,
            'duration': 2.0
        },
        {
            'text': 'The digital control systems make those old tactics look primitive.',
            'start': 2.0,
            'duration': 2.0
        }
    ]

@pytest.fixture
def mock_video_data():
    """Provide mock video data."""
    return {
        'video_id': 'test_video',
        'title': 'Test Video',
        'description': 'Testing manipulation patterns across time',
        'published_at': datetime.now().isoformat()
    }

@pytest.fixture
def pattern_detection_state(base_state):
    """Provide state configured for pattern detection testing."""
    state = base_state.copy()
    state.messages.current_message = """
    The mainstream media's sudden shift to positive crypto coverage is suspicious.
    The same outlets that were spreading FUD last month are now pumping Bitcoin.
    This looks like coordinated narrative manipulation.
    """
    state.analysis.entities = [
        {
            'type': 'cryptocurrency',
            'text': 'Bitcoin',
            'timestamp': datetime.now().isoformat()
        }
    ]
    return state