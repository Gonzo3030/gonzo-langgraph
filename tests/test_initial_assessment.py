import pytest
from langchain_core.messages import HumanMessage
from gonzo.types import GonzoState
from gonzo.states.initial_assessment import initial_assessment

def test_initial_assessment_crypto():
    # Create test state
    state = GonzoState(
        messages=[HumanMessage(content="What's happening with Bitcoin today?")],
        current_step="initial",
        context={},
        intermediate_steps=[],
        assistant_message=None,
        tools={},
        errors=[]
    )
    
    # Run assessment
    new_state = initial_assessment(state)
    
    # Check results
    assert "crypto" in new_state["context"]["category"].lower()
    assert len(new_state["intermediate_steps"]) > 0
    assert not new_state["errors"]

def test_initial_assessment_narrative():
    # Create test state
    state = GonzoState(
        messages=[HumanMessage(content="How is social media manipulating the narrative?")],
        current_step="initial",
        context={},
        intermediate_steps=[],
        assistant_message=None,
        tools={},
        errors=[]
    )
    
    # Run assessment
    new_state = initial_assessment(state)
    
    # Check results
    assert "narrative" in new_state["context"]["category"].lower()
    assert len(new_state["intermediate_steps"]) > 0
    assert not new_state["errors"]