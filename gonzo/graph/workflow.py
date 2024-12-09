from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import RoutingEdge
from pydantic import BaseModel

from ..types import GonzoState, NextStep

StateType = TypeVar("StateType", bound=BaseModel)

def should_route_to_narrative(state: GonzoState) -> bool:
    return state.next_step == NextStep.NARRATIVE

def should_route_to_crypto(state: GonzoState) -> bool:
    return state.next_step == NextStep.CRYPTO

def should_route_to_general(state: GonzoState) -> bool:
    return state.next_step == NextStep.GENERAL

def should_route_to_error(state: GonzoState) -> bool:
    return state.next_step == NextStep.ERROR

def should_end(state: GonzoState) -> bool:
    return state.next_step == NextStep.END

def create_router() -> RoutingEdge:
    """Create a routing edge for workflow control."""
    return RoutingEdge(
        conditions={
            "narrative": should_route_to_narrative,
            "crypto": should_route_to_crypto,
            "general": should_route_to_general,
            "error": should_route_to_error,
            END: should_end
        }
    )

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes for workflow steps
    workflow.add_node("assessment", lambda x: x)
    workflow.add_node("narrative", lambda x: x)
    
    # Create router
    router = create_router()
    workflow.add_node("router", router)
    
    # Set up workflow
    workflow.set_entry_point("assessment")
    
    # Configure edges
    workflow.add_edge("assessment", "router")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "router",
        {
            "narrative": "narrative",
            "crypto": END,  # For now, end on crypto
            "general": END,  # For now, end on general
            "error": END,
            END: END
        }
    )
    
    # Add final edges
    workflow.add_edge("narrative", END)
    
    return workflow.compile()