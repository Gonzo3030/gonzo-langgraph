import pytest
from unittest.mock import AsyncMock, patch
from langchain.schema import HumanMessage
from gonzo.nodes.new_assessment import assess_input
from gonzo.graph.state import GonzoState

@pytest.fixture
def state():
    return GonzoState()

@pytest.fixture
def mock_chain():
    return AsyncMock(return_value="CRYPTO")

@pytest.mark.asyncio
async def test_assess_input_no_messages(state):
    """Test assessment with no messages."""
    result = await assess_input(state)
    
    assert result["next"] == "error"
    assert state.state["errors"] is not None
    assert "No messages" in state.state["errors"][0]

@pytest.mark.asyncio
async def test_assess_input_crypto(state, mock_chain):
    """Test assessment with crypto message."""
    state.add_message(HumanMessage(content="Bitcoin price analysis"))
    
    with patch("gonzo.nodes.new_assessment.chain.invoke", mock_chain):
        result = await assess_input(state)
        
        assert result["next"] == "crypto"
        assert state.state["next_step"] == "crypto"
        
        memory_result = state.get_from_memory("last_assessment")
        assert memory_result["category"] == "crypto"

@pytest.mark.asyncio
async def test_assess_input_error_handling(state):
    """Test assessment error handling."""
    state.add_message(HumanMessage(content="Test message"))
    
    async def mock_error(*args, **kwargs):
        raise ValueError("Test error")
    
    with patch("gonzo.nodes.new_assessment.chain.invoke", mock_error):
        result = await assess_input(state)
        
        assert result["next"] == "error"
        assert state.state["errors"] is not None
        assert "Test error" in state.state["errors"][0]
        
        error_info = state.get_from_memory("last_error")
        assert error_info["node"] == "assessment"
        assert "Test error" in error_info["error"]

@pytest.mark.asyncio
async def test_assess_input_invalid_category(state):
    """Test assessment with invalid category response."""
    state.add_message(HumanMessage(content="Test message"))
    
    with patch("gonzo.nodes.new_assessment.chain.invoke", AsyncMock(return_value="INVALID")):
        result = await assess_input(state)
        
        assert result["next"] == "general"
        
        memory_result = state.get_from_memory("last_assessment")
        assert memory_result["category"] == "general"
        assert memory_result["raw_category"] == "INVALID"