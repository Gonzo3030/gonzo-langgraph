import pytest
from langchain_core.messages import HumanMessage
from gonzo.types import GonzoState
from gonzo.states.initial_assessment import initial_assessment

def create_test_state(message_content: str) -> GonzoState:
    """Helper function to create a test state."""
    return GonzoState(
        messages=[HumanMessage(content=message_content)],
        current_step="initial",
        context={},
        intermediate_steps=[],
        assistant_message=None,
        tools={},
        errors=[]
    )

def test_initial_assessment_crypto():
    # Create test state
    state = create_test_state("What's happening with Bitcoin today?")
    
    # Run assessment
    new_state = initial_assessment(state)
    
    # Check results
    assert "context" in new_state
    assert "category" in new_state["context"]
    assert "crypto" in new_state["context"]["category"].lower()
    assert len(new_state["intermediate_steps"]) > 0
    assert not new_state["errors"]

def test_initial_assessment_narrative():
    # Create test state
    state = create_test_state("How is social media manipulating the narrative?")
    
    # Run assessment
    new_state = initial_assessment(state)
    
    # Check results
    assert "context" in new_state
    assert "category" in new_state["context"]
    assert "narrative" in new_state["context"]["category"].lower()
    assert len(new_state["intermediate_steps"]) > 0
    assert not new_state["errors"]

def test_initial_assessment_error_handling():
    # Create invalid state to test error handling
    state = GonzoState(
        messages=[],  # Empty messages should cause an error
        current_step="initial",
        context={},
        intermediate_steps=[],
        assistant_message=None,
        tools={},
        errors=[]
    )
    
    # Run assessment
    new_state = initial_assessment(state)
    
    # Check error handling
    assert "context" in new_state
    assert "category" in new_state["context"]
    assert new_state["context"]["category"] == "general"  # Default category on error
    assert len(new_state["errors"]) > 0