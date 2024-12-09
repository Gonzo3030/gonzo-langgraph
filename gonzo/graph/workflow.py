from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import RoutingEdge
from pydantic import BaseModel

from ..types import GonzoState, NextStep
from ..nodes.knowledge_enhanced_assessment import enhance_assessment
from ..nodes.knowledge_enhanced_narrative import enhance_narrative

StateType = TypeVar("StateType", bound=BaseModel)

def create_router() -> RoutingEdge:
    """Create a routing edge for workflow control."""
    return RoutingEdge(
        conditions={
            "narrative": lambda x: x.next_step == NextStep.NARRATIVE,
            "crypto": lambda x: x.next_step == NextStep.CRYPTO,
            "general": lambda x: x.next_step == NextStep.GENERAL,
            "error": lambda x: x.next_step == NextStep.ERROR,
            END: lambda x: x.next_step == NextStep.END
        }
    )

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes for workflow steps
    workflow.add_node("assessment", enhance_assessment)
    workflow.add_node("narrative", enhance_narrative)
    
    # Create router
    router = create_router()
    workflow.add_node("router", router)
    
    # Set up workflow
    workflow.set_entry_point("assessment")
    
    # Configure edges
    workflow.add_edge("assessment", "router")
    
    # Add conditional routing
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