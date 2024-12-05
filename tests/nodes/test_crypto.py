import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from langchain.schema import HumanMessage
from gonzo.nodes.new_crypto import analyze_crypto, analysis_chain
from gonzo.graph.state import GonzoState

# Test data
SAMPLE_ANALYSIS = """🏦 MARKET ANALYSIS
Bullish momentum with strong volume.

📊 TECHNICAL INDICATORS
All indicators point up.

🌊 SOCIAL SENTIMENT
Very positive community feedback.

⚖️ REGULATORY LANDSCAPE
Regulators seem supportive.

🔮 FUTURE IMPLICATIONS
Long-term outlook positive."""

@pytest.fixture
def state():
    return GonzoState()

@pytest.fixture
def mock_chain():
    mock = AsyncMock()
    mock.ainvoke.return_value = {"output": SAMPLE_ANALYSIS}
    return mock

@pytest.mark.asyncio
async def test_analyze_crypto_no_messages(state):
    """Test crypto analysis with no messages."""
    result = await analyze_crypto(state)
    
    assert result["next"] == "error"
    assert state.state["errors"] is not None
    assert "No messages" in state.state["errors"][0]

@pytest.mark.asyncio
async def test_analyze_crypto_success(state, mock_chain, monkeypatch):
    """Test successful crypto analysis."""
    state.add_message(HumanMessage(content="Analyze BTC market"))
    monkeypatch.setattr("gonzo.nodes.new_crypto.analysis_chain", mock_chain)
    
    result = await analyze_crypto(state)
    
    assert result["next"] == "respond"
    assert state.state["next_step"] == "respond"
    assert "💰 GONZO CRYPTO DISPATCH" in result["response"]
    
    # Check memory storage - note we're using long-term memory
    memory_result = state.get_from_memory("last_crypto_analysis", "long_term")
    assert memory_result is not None
    assert memory_result["raw_analysis"] == SAMPLE_ANALYSIS
    
    # Print debug info
    print(f"\nState memory: {state.state['memory']}")
    print(f"Memory result: {memory_result}")