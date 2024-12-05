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
    
    # Check memory storage
    memory_result = state.get_from_memory("last_crypto_analysis")
    assert memory_result["raw_analysis"] == SAMPLE_ANALYSIS
    assert all(section in memory_result["structured_report"] 
              for section in ["🏦 MARKET ANALYSIS", "📊 TECHNICAL INDICATORS"])
    assert isinstance(memory_result["tweet_thread"], list)
    
    mock_chain.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_crypto_error_handling(state, monkeypatch):
    """Test crypto analysis error handling."""
    state.add_message(HumanMessage(content="Test message"))
    
    error_chain = AsyncMock()
    error_chain.ainvoke.side_effect = ValueError("Test error")
    monkeypatch.setattr("gonzo.nodes.new_crypto.analysis_chain", error_chain)
    
    result = await analyze_crypto(state)
    
    assert result["next"] == "error"
    assert state.state["errors"] is not None
    assert "Test error" in state.state["errors"][0]
    
    error_info = state.get_from_memory("last_error")
    assert error_info["node"] == "crypto"
    assert "Test error" in error_info["error"]
    assert "timeline" in result["response"].lower()

@pytest.mark.asyncio
async def test_crypto_report_structure(state, mock_chain, monkeypatch):
    """Test structure of generated crypto report."""
    state.add_message(HumanMessage(content="Analyze crypto market"))
    monkeypatch.setattr("gonzo.nodes.new_crypto.analysis_chain", mock_chain)
    
    result = await analyze_crypto(state)
    memory_result = state.get_from_memory("last_crypto_analysis")
    
    report = memory_result["structured_report"]
    assert len(report) == 5  # All sections present
    assert all(section.strip() for section in report.values())  # No empty sections
    
    thread = memory_result["tweet_thread"]
    assert all(tweet.startswith("💰") for tweet in thread)  # Proper tweet formatting
    assert all(len(tweet) <= 280 for tweet in thread)  # Tweet length constraint