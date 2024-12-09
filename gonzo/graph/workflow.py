from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import RoutingEdge
from pydantic import BaseModel

from ..types import GonzoState
from ..nodes.knowledge_enhanced_assessment import enhance_assessment
from ..nodes.knowledge_enhanced_narrative import enhance_narrative

StateType = TypeVar("StateType", bound=BaseModel)

def create_router() -> RoutingEdge:
    """Create a routing edge for workflow control."""
    return RoutingEdge(
        conditions={
            "narrative": lambda x: x.next_step == "narrative",
            END: lambda x: x.next_step != "narrative"
        }
    )

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes for the main workflow steps
    workflow.add_node("assessment", enhance_assessment)
    workflow.add_node("narrative", enhance_narrative)
    
    # Create router
    router = create_router()
    
    # Set up the workflow
    workflow.add_node("router", router)
    
    # Configure edges
    workflow.set_entry_point("assessment")
    workflow.add_edge("assessment", "router")
    workflow.add_conditional_edges(
        "router",
        {"narrative": "narrative", END: END}
    )
    workflow.add_edge("narrative", END)
    
    return workflow.compile()