import pytest
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from gonzo.nodes.assessment import assess_input
from gonzo.types import GonzoState, create_initial_state, update_state

def test_assessment_crypto():
    # Arrange
    initial_state = create_initial_state(
        HumanMessage(content="What's happening with Bitcoin today?")
    )
    
    # Act
    updates = assess_input(initial_state)
    final_state = update_state(initial_state, updates)
    
    # Assert
    assert final_state["category"] == "crypto"
    assert len(final_state["steps"]) == 1
    assert final_state["steps"][0]["node"] == "assessment"
    assert "assessment_timestamp" in final_state["context"]
    assert "raw_category" in final_state["context"]
    
def test_assessment_narrative():
    # Arrange
    initial_state = create_initial_state(
        HumanMessage(content="How is social media manipulating the narrative?")
    )
    
    # Act
    updates = assess_input(initial_state)
    final_state = update_state(initial_state, updates)
    
    # Assert
    assert final_state["category"] == "narrative"
    assert len(final_state["steps"]) == 1
    assert final_state["steps"][0]["node"] == "assessment"
    assert "assessment_timestamp" in final_state["context"]
    
def test_assessment_general():
    # Arrange
    initial_state = create_initial_state(
        HumanMessage(content="What's the weather like today?")
    )
    
    # Act
    updates = assess_input(initial_state)
    final_state = update_state(initial_state, updates)
    
    # Assert
    assert final_state["category"] == "general"
    assert len(final_state["steps"]) == 1
    
def test_assessment_error_handling():
    # Arrange - create invalid state
    invalid_state = GonzoState(
        messages=[],
        context={},
        steps=[],
        timestamp="2024-01-01T00:00:00",
        category="",
        response=""
    )
    
    # Act
    updates = assess_input(invalid_state)
    final_state = update_state(invalid_state, updates)
    
    # Assert
    assert final_state["category"] == "general"
    assert len(final_state["steps"]) == 1
    assert "error" in final_state["steps"][0]
    assert "assessment_error" in final_state["context"]

def test_create_initial_state_with_string():
    # Test creating state with string input
    state = create_initial_state("hello")
    assert len(state["messages"]) == 1
    assert state["messages"][0].content == "hello"
    
def test_create_initial_state_with_message():
    # Test creating state with HumanMessage input
    msg = HumanMessage(content="hello")
    state = create_initial_state(msg)
    assert len(state["messages"]) == 1
    assert state["messages"][0] == msg