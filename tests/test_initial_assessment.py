import pytest
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from gonzo.types import MessagesState
from gonzo.states.initial_assessment import initial_assessment
from gonzo.config import SYSTEM_PROMPT

def create_test_state(message_content: str) -> MessagesState:
    """Helper function to create a test state."""
    return MessagesState(
        messages=[
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=message_content)
        ],
        current_step="initial",
        context={},
        intermediate_steps=[],
        assistant_message=None,
        tools={},
        errors=[]
    )

def update_state(state: MessagesState, updates: Dict[str, Any]) -> MessagesState:
    """Helper function to update state with node results."""
    new_state = state.copy()
    
    # Update messages
    if "messages" in updates:
        new_state["messages"].extend(updates["messages"])
    
    # Update context
    if "context" in updates:
        new_state["context"].update(updates["context"])
    
    # Update intermediate steps
    if "intermediate_steps" in updates:
        new_state["intermediate_steps"].extend(updates["intermediate_steps"])
    
    # Update errors
    if "errors" in updates:
        new_state["errors"].extend(updates["errors"])
    
    return new_state

def test_initial_assessment_crypto():
    # Create test state
    state = create_test_state("What's happening with Bitcoin today?")
    
    # Run assessment
    updates = initial_assessment(state)
    new_state = update_state(state, updates)
    
    # Check results
    assert "category" in new_state["context"]
    assert new_state["context"]["category"] == "CRYPTO"
    assert len(new_state["intermediate_steps"]) > 0
    assert not new_state["errors"]

def test_initial_assessment_narrative():
    # Create test state
    state = create_test_state("How is social media manipulating the narrative?")
    
    # Run assessment
    updates = initial_assessment(state)
    new_state = update_state(state, updates)
    
    # Check results
    assert "category" in new_state["context"]
    assert new_state["context"]["category"] == "NARRATIVE"
    assert len(new_state["intermediate_steps"]) > 0
    assert not new_state["errors"]

def test_initial_assessment_error_handling():
    # Create invalid state to test error handling
    state = MessagesState(
        messages=[],  # Empty messages should cause an error
        current_step="initial",
        context={},
        intermediate_steps=[],
        assistant_message=None,
        tools={},
        errors=[]
    )
    
    # Run assessment
    updates = initial_assessment(state)
    new_state = update_state(state, updates)
    
    # Check error handling
    assert "category" in new_state["context"]
    assert new_state["context"]["category"] == "GENERAL"  # Default category on error
    assert len(new_state["errors"]) > 0