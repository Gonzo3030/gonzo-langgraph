import pytest
from pathlib import Path
import asyncio
from datetime import datetime, UTC
from tests.mocks.llm import MockLLM
from gonzo.collectors.youtube import YouTubeCollector
from gonzo.evolution import GonzoEvolutionSystem
from gonzo.prompts.dynamic import DynamicPromptSystem
from gonzo.response.types import ResponseType, ResponseTypeManager
from gonzo.interaction.state import InteractionStateManager
from gonzo.context.time_periods import TimePeriodManager

@pytest.fixture
def test_storage_path(tmp_path):
    return tmp_path / "test_storage"

@pytest.fixture
def mock_llm():
    return MockLLM()

@pytest.fixture
def evolution_system(mock_llm, test_storage_path):
    return GonzoEvolutionSystem(
        llm=mock_llm,
        storage_path=test_storage_path
    )

@pytest.fixture
def youtube_collector(mock_llm, evolution_system):
    return YouTubeCollector(
        agent=mock_llm,
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

# ... [rest of the test file remains the same] ...