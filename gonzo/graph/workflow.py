from typing import Annotated
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, Graph
from ..types import GonzoState
from ..config import SYSTEM_PROMPT
from .nodes import (
    initial_assessment,
    crypto_analysis,
    narrative_detection,
    response_generation
)

def create_initial_state(user_input: str) -> GonzoState:
    """Create initial state for the Gonzo workflow."""
    return GonzoState(
        messages=[SystemMessage(content=SYSTEM_PROMPT),
                 HumanMessage(content=user_input)],
        current_step="initial_assessment",
        context={},
        intermediate_steps=[],
        assistant_message=None,
        tools={},
        errors=[]
    )

def next_step_router(state: GonzoState) -> str:
    """Determine the next step in the workflow."""
    category = state["context"].get("category")
    
    if state["errors"]:
        return "response_generation"
    
    if category == "crypto":
        return "crypto_analysis"
    elif category == "narrative":
        return "narrative_detection"
    
    return "response_generation"

def create_graph() -> Graph:
    """Create the Gonzo workflow graph."""
    # Create graph with our state type
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("initial_assessment", initial_assessment)
    workflow.add_node("crypto_analysis", crypto_analysis)
    workflow.add_node("narrative_detection", narrative_detection)
    workflow.add_node("response_generation", response_generation)
    
    # Add edges
    workflow.add_edge("initial_assessment", next_step_router)
    workflow.add_edge("crypto_analysis", "response_generation")
    workflow.add_edge("narrative_detection", "response_generation")
    
    # Set entry point
    workflow.set_entry_point("initial_assessment")
    
    # Compile graph
    return workflow.compile()