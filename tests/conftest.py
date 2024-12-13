"""Test configuration and fixtures."""

import pytest
from pathlib import Path
from datetime import datetime
from .mocks.llm import MockLLM
from gonzo.patterns.detector import PatternDetector
from gonzo.evolution import GonzoEvolutionSystem

@pytest.fixture
def mock_llm():
    """Provide mock language model."""
    return MockLLM()

@pytest.fixture
def test_storage_path(tmp_path):
    """Provide test storage path."""
    return tmp_path / "test_storage"

@pytest.fixture
def pattern_detector():
    """Provide pattern detector."""
    return PatternDetector()

@pytest.fixture
def evolution_system(mock_llm, pattern_detector, test_storage_path):
    """Provide evolution system."""
    return GonzoEvolutionSystem(
        llm=mock_llm,
        pattern_detector=pattern_detector,
        storage_path=test_storage_path
    )

@pytest.fixture
def mock_transcript_data():
    """Provide mock transcript data."""
    return [
        {
            'text': 'This reeks of the same manipulation we fought in the 60s',
            'start': 0.0,
            'duration': 2.0
        },
        {
            'text': 'The corporate control systems have just gone digital',
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
        'description': 'Testing corporate control patterns',
        'published_at': datetime.now().isoformat()
    }