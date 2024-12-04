from typing import Dict, TypeVar, Annotated
from langgraph.graph import StateGraph, Graph
from pydantic import BaseModel
from ..types import AgentState
from .nodes import initial_assessment, crypto_analysis, narrative_detection, response_generation

AgentStateT = TypeVar("AgentStateT", bound=AgentState)

def create_workflow() -> Graph:
    """Create the Gonzo agent workflow graph."""
    # Initialize the graph with our Pydantic state type
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("initial", initial_assessment)
    workflow.add_node("crypto", crypto_analysis)
    workflow.add_node("narrative", narrative_detection)
    workflow.add_node("response", response_generation)
    
    # Define conditional state router
    def route_next_step(state: AgentState) -> str:
        # Route based on category and errors
        if state.errors:
            return "response"
            
        category = state.context.get("category", "general")
        if category == "crypto":
            return "crypto"
        elif category == "narrative":
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