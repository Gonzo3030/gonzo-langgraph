from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState, NextStep

StateType = TypeVar("StateType", bound=BaseModel)

def route_next_step(state: GonzoState) -> Dict[str, Any]:
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
    
    # Return the state and the next step
    return {"next": next_steps.get(state.next_step, "error")}

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("start", lambda x: x)
    workflow.add_node("assessment", lambda x: x)
    workflow.add_node("narrative", lambda x: x)
    workflow.add_node("router", route_next_step)
    
    # Set up workflow
    workflow.set_entry_point("start")
    
    # Add edges
    workflow.add_edge("start", "assessment")
    workflow.add_edge("assessment", "router")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "router",
        {
            "narrative": "narrative",
            "end": END,
            "error": END
        },
        key="next"
    )
    
    # Add final edges
    workflow.add_edge("narrative", END)
    
    return workflow.compile()