from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState, NextStep

StateType = TypeVar("StateType", bound=BaseModel)

def route_next_step(state: GonzoState) -> str:
    """Determine the next step in the workflow."""
    if not state.next_step:
        return "assessment"
        
    # Map enum values to workflow steps
    step_map = {
        NextStep.NARRATIVE: "narrative",
        NextStep.CRYPTO: "end",  # For now, end on crypto
        NextStep.GENERAL: "end",  # For now, end on general
        NextStep.ERROR: "end",
        NextStep.END: "end"
    }
    
    return step_map.get(state.next_step, "error")

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes for workflow steps
    workflow.add_node("assessment", lambda x: x)
    workflow.add_node("narrative", lambda x: x)
    
    # Set up workflow
    workflow.set_entry_point("assessment")
    
    # Add conditional edges using the route_next_step function
    workflow.add_edge("assessment", route_next_step)
    workflow.add_edge("narrative", route_next_step)
    
    return workflow.compile()