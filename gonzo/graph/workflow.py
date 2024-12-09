from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import RoutingEdge
from pydantic import BaseModel

from ..types import GonzoState
from ..nodes.knowledge_enhanced_assessment import enhance_assessment
from ..nodes.knowledge_enhanced_narrative import enhance_narrative

StateType = TypeVar("StateType", bound=BaseModel)

def should_route_to_narrative(state: GonzoState) -> bool:
    """Determine if we should route to narrative generation."""
    return state.next_step == "narrative"

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes for the main workflow steps
    workflow.add_node("assessment", enhance_assessment)
    workflow.add_node("narrative", enhance_narrative)
    
    # Set up branching logic
    workflow.add_edge("assessment", "narrative", should_route_to_narrative)
    workflow.add_edge("assessment", END, lambda x: not should_route_to_narrative(x))
    workflow.add_edge("narrative", END)
    
    # Set the entry point
    workflow.set_entry_point("assessment")
    
    return workflow.compile()