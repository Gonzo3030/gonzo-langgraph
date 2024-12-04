from typing import Dict, Any
from langgraph.graph import StateGraph, Graph
from ..types import GonzoState
from ..nodes.assessment import assess_input

def create_workflow() -> Graph:
    """Create the Gonzo agent workflow graph."""
    # Initialize the graph with our state type
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("assessment", assess_input)
    
    # Define conditional router
    def route_next(state: GonzoState) -> str:
        category = state["category"]
        if category == "crypto":
            return "crypto"
        elif category == "narrative":
            return "narrative"
        return "response"
    
    # Add edges with conditional routing
    workflow.add_edge("assessment", route_next)
    
    # Set entry point
    workflow.set_entry_point("assessment")
    
    # Compile graph
    return workflow.compile()