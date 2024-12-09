from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState, NextStep

StateType = TypeVar("StateType", bound=BaseModel)

def handle_assessment(state: GonzoState) -> Dict[str, Any]:
    """Assessment node handler."""
    # Implement assessment logic here
    return {"state": state}

def handle_narrative(state: GonzoState) -> Dict[str, Any]:
    """Narrative analysis handler."""
    # Implement narrative analysis logic here
    return {"state": state}

def router(state: GonzoState) -> str:
    """Router node for the workflow.
    Returns the next node name as a string instead of using lambda.
    """
    if not state.next_step:
        state.next_step = NextStep.NARRATIVE
    
    next_steps = {
        NextStep.NARRATIVE: "narrative",
        NextStep.CRYPTO: "end",
        NextStep.GENERAL: "end",
        NextStep.ERROR: "end",
        NextStep.END: "end"
    }
    
    return next_steps.get(state.next_step, "end")

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph using updated LangGraph patterns."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes with their respective handlers
    workflow.add_node("start", lambda x: {"state": x})
    workflow.add_node("assessment", handle_assessment)
    workflow.add_node("narrative", handle_narrative)
    workflow.add_node("end", lambda x: {"state": x})
    
    # Set up the entry point
    workflow.set_entry_point("start")
    
    # Add conditional edges with explicit node names
    workflow.add_conditional_edges(
        "start",
        # Return next node name based on state
        lambda x: "assessment",
        {
            "assessment": "assessment"
        }
    )
    
    workflow.add_conditional_edges(
        "assessment",
        router,  # Use router function to determine next node
        {
            "narrative": "narrative",
            "end": "end"
        }
    )
    
    workflow.add_conditional_edges(
        "narrative",
        router,  # Use router function again for next step
        {
            "narrative": "narrative",
            "end": "end"
        }
    )
    
    return workflow.compile()
