import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain.schema import HumanMessage
from gonzo.nodes.new_assessment import assess_input, assessment_chain
from gonzo.graph.state import GonzoState

@pytest.fixture
def state():
    return GonzoState()

@pytest.fixture
def mock_chain():
    mock = AsyncMock()
    mock.ainvoke.return_value = {"output": "CRYPTO"}
    return mock

@pytest.mark.asyncio
async def test_assess_input_no_messages(state):
    """Test assessment with no messages."""
    result = await assess_input(state)
    
    assert result["next"] == "error"
    assert state.state["errors"] is not None
    assert "No messages" in state.state["errors"][0]

@pytest.mark.asyncio
async def test_assess_input_crypto(state, mock_chain, monkeypatch):
    """Test assessment with crypto message."""
    state.add_message(HumanMessage(content="Bitcoin price analysis"))
    monkeypatch.setattr("gonzo.nodes.new_assessment.assessment_chain", mock_chain)
    
    result = await assess_input(state)
    
    assert result["next"] == "crypto"
    assert state.state["next_step"] == "crypto"
    
    memory_result = state.get_from_memory("last_assessment")
    assert memory_result["category"] == "crypto"
    
    mock_chain.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_assess_input_error_handling(state, monkeypatch):
    """Test assessment error handling."""
    state.add_message(HumanMessage(content="Test message"))
    
    error_chain = AsyncMock()
    error_chain.ainvoke.side_effect = ValueError("Test error")
    monkeypatch.setattr("gonzo.nodes.new_assessment.assessment_chain", error_chain)
    
    result = await assess_input(state)
    
    assert result["next"] == "error"
    assert state.state["errors"] is not None
    assert "Test error" in state.state["errors"][0]
    
    error_info = state.get_from_memory("last_error")
    assert error_info["node"] == "assessment"
    assert "Test error" in error_info["error"]

@pytest.mark.asyncio
async def test_assess_input_invalid_category(state, monkeypatch):
    """Test assessment with invalid category response."""
    state.add_message(HumanMessage(content="Test message"))
    
    invalid_chain = AsyncMock()
    invalid_chain.ainvoke.return_value = {"output": "INVALID"}
    monkeypatch.setattr("gonzo.nodes.new_assessment.assessment_chain", invalid_chain)
    
    result = await assess_input(state)
    
    assert result["next"] == "general"
    
    memory_result = state.get_from_memory("last_assessment")
    assert memory_result["category"] == "general"
    assert memory_result["raw_category"] == "INVALID"