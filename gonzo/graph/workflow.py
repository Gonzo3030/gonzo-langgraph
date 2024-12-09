from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState, NextStep

StateType = TypeVar("StateType", bound=BaseModel)

def router(state: GonzoState) -> Dict[str, Any]:
    """Router node for the workflow."""
    if not state.next_step:
        state.next_step = NextStep.NARRATIVE
    
    next_steps = {
        NextStep.NARRATIVE: "narrative",
        NextStep.CRYPTO: END,
        NextStep.GENERAL: END,
        NextStep.ERROR: END,
        NextStep.END: END
    }
    
    next_step = next_steps.get(state.next_step, END)
    return {"state": state, "next": next_step}

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("start", lambda x: x)
    workflow.add_node("assessment", lambda x: x)
    workflow.add_node("router", router)
    workflow.add_node("narrative", lambda x: x)
    
    # Set up workflow
    workflow.set_entry_point("start")
    
    # Add base edges
    workflow.add_edge("start", "assessment")
    workflow.add_edge("assessment", "router")
    workflow.add_edge("narrative", "router")
    workflow.add_edge("router", lambda x: x["next"])
    
    return workflow.compile()