import pytest
import asyncio
from datetime import datetime, timedelta

from tests.mocks.llm import MockLLM
from gonzo.types import GonzoState
from gonzo.nodes.pattern_detection import detect_patterns

@pytest.fixture
def mock_llm():
    return MockLLM()

@pytest.mark.asyncio
async def test_assessment_knowledge_flow(mock_llm):
    # Create initial state with a crypto-related message
    state = GonzoState()
    state.messages.current_message = """
    Bitcoin just hit a new all-time high amidst massive institutional buying.
    The market sentiment has completely flipped from last month's bearish trend.
    Major banks are now announcing crypto custody services.
    """
    
    # Add some initial analysis
    state.analysis.entities.append({
        "type": "cryptocurrency",
        "text": "Bitcoin",
        "timestamp": datetime.now().isoformat()
    })
    
    # Run pattern detection
    result = await detect_patterns(state, mock_llm)
    
    # Verify the flow continues to analysis
    assert result["next"] == "analyze"
    
    # Verify patterns were detected
    assert len(state.analysis.patterns) > 0
    
    # Verify significance was updated
    assert state.analysis.significance > 0
    
    # Add a related manipulation message
    state.messages.current_message = """
    The mainstream media's sudden shift to positive crypto coverage is suspicious.
    The same outlets that were spreading FUD last month are now pumping Bitcoin.
    This looks like coordinated narrative manipulation.
    """
    
    # Run second detection
    result2 = await detect_patterns(state, mock_llm)
    
    # Verify more patterns found
    assert len(state.analysis.patterns) > 1
    
    # Verify significance increased
    assert state.analysis.significance > 0.5  # Higher significance for manipulation pattern
    
    return state