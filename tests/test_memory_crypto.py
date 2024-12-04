import pytest
from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage
from gonzo.nodes.memory_enhanced_crypto import analyze_crypto_with_memory
from gonzo.types import GonzoState, create_initial_state
from tests.mocks.mock_memory import MockMemoryInterface

@pytest.fixture
def mock_memory():
    return MockMemoryInterface()

@pytest.fixture
def basic_state():
    return create_initial_state(
        HumanMessage(content="What's your take on the latest crypto market rally?")
    )

@pytest.mark.asyncio
async def test_crypto_analysis_with_memories(basic_state, mock_memory):
    # Act
    updates = await analyze_crypto_with_memory(basic_state, mock_memory)
    
    # Print analysis for inspection
    print("\nGonzo Analysis with Memories:\n" + "=" * 50)
    print(updates["response"])
    print("=" * 50 + "\n")
    
    # Assert structure
    assert "crypto_analysis" in updates["context"]
    assert "structured_report" in updates["context"]
    assert "tweet_thread" in updates["context"]
    assert "relevant_memories" in updates["context"]
    
    # Verify memories were used
    memories = updates["context"]["relevant_memories"]
    assert len(memories["pre_1974"]) > 0
    assert len(memories["dark_period"]) > 0
    assert len(memories["future"]) > 0
    
    # Check if new memory was stored
    stored = mock_memory.get_stored_memories()
    assert len(stored) == 1
    assert stored[0].category == "crypto"

@pytest.mark.asyncio
async def test_memory_enhanced_crash_analysis(mock_memory):
    # Arrange
    crash_state = create_initial_state(
        HumanMessage(content="The crypto market just crashed 40% in 24 hours! What's really happening?")
    )
    
    # Act
    updates = await analyze_crypto_with_memory(crash_state, mock_memory)
    
    print("\nCrash Analysis with Memories:\n" + "=" * 50)
    print(updates["response"])
    print("=" * 50 + "\n")
    
    # Verify memory integration
    assert "relevant_memories" in updates["context"]
    assert "2027: The Great Crypto Schism" in any(
        m.content for m in updates["context"]["relevant_memories"]["future"]
    )
    
    # Check analysis content
    analysis = updates["context"]["crypto_analysis"].lower()
    assert any(term in analysis for term in ["crash", "liquidation", "panic", "whale", "manipulation"])
    
    # Verify structured sections
    report = updates["context"]["structured_report"]
    assert len(report) >= 3

@pytest.mark.asyncio
async def test_memory_storage(mock_memory):
    # Arrange
    state = create_initial_state(
        HumanMessage(content="Tell me about institutional adoption in crypto.")
    )
    
    # Act
    await analyze_crypto_with_memory(state, mock_memory)
    
    # Verify memory storage
    stored = mock_memory.get_stored_memories()
    assert len(stored) == 1
    assert isinstance(stored[0].timestamp, datetime)
    assert "report" in stored[0].metadata

@pytest.mark.asyncio
async def test_error_handling_with_memory(mock_memory):
    # Arrange - create invalid state
    invalid_state = create_initial_state("")
    invalid_state["messages"] = []
    
    # Act
    updates = await analyze_crypto_with_memory(invalid_state, mock_memory)
    
    # Assert
    assert "crypto_error" in updates["context"]
    assert len(updates["steps"]) == 1
    assert "error" in updates["steps"][0]
    assert "neural networks" in updates["response"].lower()