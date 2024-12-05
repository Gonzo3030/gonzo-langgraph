import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from langchain.schema import HumanMessage
from gonzo.nodes.new_narrative import analyze_narrative, analysis_chain
from gonzo.graph.state import GonzoState

# Test data
SAMPLE_ANALYSIS = """Listen up, you reality-blind sheep of 2024! I've seen where this twisted narrative leads, and it's a nightmare wrapped in a fever dream, served with a side of corporate-sponsored delusion.

The power brokers are playing their usual game - manufacturing consent through a toxic cocktail of fear and misinformation. They're not even trying to hide it anymore, just drowning truth in an ocean of deliberate chaos.

It's like watching a snake eat its own tail while trying to convince you it's a gourmet meal. Pure, uncut propaganda flowing through the mainstream veins of society."""

@pytest.fixture
def state():
    return GonzoState()

@pytest.fixture
def mock_chain():
    mock = AsyncMock()
    mock.ainvoke.return_value = {"output": SAMPLE_ANALYSIS}
    return mock

@pytest.mark.asyncio
async def test_analyze_narrative_no_messages(state):
    """Test narrative analysis with no messages."""
    result = await analyze_narrative(state)
    
    assert result["next"] == "error"
    assert state.state["errors"] is not None
    assert "No messages" in state.state["errors"][0]

@pytest.mark.asyncio
async def test_analyze_narrative_success(state, mock_chain, monkeypatch):
    """Test successful narrative analysis."""
    state.add_message(HumanMessage(content="Analyze this media narrative"))
    monkeypatch.setattr("gonzo.nodes.new_narrative.analysis_chain", mock_chain)
    
    result = await analyze_narrative(state)
    
    assert result["next"] == "respond"
    assert state.state["next_step"] == "respond"
    assert "🔥 GONZO DISPATCH" in result["response"]
    
    # Check memory storage
    memory_result = state.get_from_memory("last_narrative_analysis", "long_term")
    assert memory_result is not None
    assert memory_result["raw_analysis"] == SAMPLE_ANALYSIS
    assert isinstance(memory_result["tweet_thread"], list)
    
    # Print debug info
    print(f"\nState memory: {state.state['memory']}")
    print(f"Memory result: {memory_result}")

@pytest.mark.asyncio
async def test_analyze_narrative_error_handling(state, monkeypatch):
    """Test narrative analysis error handling."""
    state.add_message(HumanMessage(content="Test message"))
    
    error_chain = AsyncMock()
    error_chain.ainvoke.side_effect = ValueError("Test error")
    monkeypatch.setattr("gonzo.nodes.new_narrative.analysis_chain", error_chain)
    
    result = await analyze_narrative(state)
    
    assert result["next"] == "error"
    assert state.state["errors"] is not None
    assert "Test error" in state.state["errors"][0]
    
    error_info = state.get_from_memory("last_error", "short_term")
    assert error_info["node"] == "narrative"
    assert "Test error" in error_info["error"]
    assert "trip" in result["response"].lower()

@pytest.mark.asyncio
async def test_narrative_thread_creation(state, mock_chain, monkeypatch):
    """Test thread creation from narrative analysis."""
    state.add_message(HumanMessage(content="Analyze this propaganda"))
    monkeypatch.setattr("gonzo.nodes.new_narrative.analysis_chain", mock_chain)
    
    result = await analyze_narrative(state)
    memory_result = state.get_from_memory("last_narrative_analysis", "long_term")
    
    thread = memory_result["tweet_thread"]
    assert all(tweet.startswith("🧵") for tweet in thread)  # Proper tweet formatting
    assert all(len(tweet) <= 280 for tweet in thread)  # Tweet length constraint