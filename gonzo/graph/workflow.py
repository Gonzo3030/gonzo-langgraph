from typing import Dict, Any, Annotated, Literal
from langgraph.graph import StateGraph, Graph
from ..types import MessagesState, Channel
from ..states import (
    initial_assessment,
    crypto_analysis,
    narrative_detection,
    response_generation
)

def create_workflow() -> Graph:
    """Create the Gonzo agent workflow graph."""
    # Initialize the graph with our state type
    workflow = StateGraph(MessagesState)
    
    # Add nodes
    workflow.add_node("initial", initial_assessment)
    workflow.add_node("crypto", crypto_analysis)
    workflow.add_node("narrative", narrative_detection)
    workflow.add_node("response", response_generation)
    
    # Define conditional state router
    def route_next_step(state: MessagesState) -> str:
        # Route based on category and errors
        if state["errors"]:
            return "response"
            
        category = state["context"].get("category", "GENERAL")
        if category == "CRYPTO":
            return "crypto"
        elif category == "NARRATIVE":
            return "narrative"
        return "response"
    
    # Add edges with conditional routing
    workflow.add_edge("initial", route_next_step)
    workflow.add_edge("crypto", "response")
    workflow.add_edge("narrative", "response")
    
    # Set entry point
    workflow.set_entry_point("initial")
    
    # Compile graph
    return workflow.compile()