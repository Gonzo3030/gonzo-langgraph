import pytest
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from gonzo.nodes.assessment import assess_input
from gonzo.types import GonzoState, create_initial_state

# Helper function to update state
def update_state(state: GonzoState, updates: Dict[str, Any]) -> GonzoState:
    """Apply updates to state copy."""
    new_state = state.copy()
    for key, value in updates.items():
        if key in new_state:
            # Handle list updates
            if isinstance(value, list) and isinstance(new_state[key], list):
                new_state[key].extend(value)
            # Handle dict updates
            elif isinstance(value, dict) and isinstance(new_state[key], dict):
                new_state[key].update(value)
            # Handle direct value updates
            else:
                new_state[key] = value
    return new_state

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
    
def test_assessment_error_handling():
    # Arrange - create invalid state
    initial_state = create_initial_state("")
    initial_state["messages"] = []
    
    # Act
    updates = assess_input(initial_state)
    final_state = update_state(initial_state, updates)
    
    # Assert
    assert final_state["category"] == "general"
    assert len(final_state["steps"]) == 1
    assert "error" in final_state["steps"][0]