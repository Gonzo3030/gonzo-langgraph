from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState, NextStep

StateType = TypeVar("StateType", bound=BaseModel)

def get_next_step(state: GonzoState) -> str:
    """Determine the next step in the workflow."""
    if not state.next_step:
        state.next_step = NextStep.NARRATIVE
    
    next_steps = {
        NextStep.NARRATIVE: "narrative",
        NextStep.CRYPTO: "end",
        NextStep.GENERAL: "end",
        NextStep.ERROR: "end",
        NextStep.END: "end"
    }
    
    return next_steps.get(state.next_step, "error")

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("start", lambda x: x)
    workflow.add_node("assessment", lambda x: x)
    workflow.add_node("narrative", lambda x: x)
    
    # Set up workflow
    workflow.set_entry_point("start")
    
    # Add edges with conditional routing
    workflow.add_edge("start", "assessment")
    workflow.add_edge("assessment", get_next_step)
    
    # Add edge from narrative to end
    workflow.add_edge("narrative", END)
    
    return workflow.compile()