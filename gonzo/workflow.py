"""Main workflow definition for Gonzo."""

from typing import Dict, Any
from langgraph.graph import StateGraph
from langchain_anthropic import ChatAnthropic

from .types import GonzoState, NextStep
from .nodes.pattern_detection import detect_patterns
from .nodes.assessment import assess_input
from .nodes.narrative import analyze_narrative

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Initialize LLM
    llm = ChatAnthropic()
    
    # Add nodes
    workflow.add_node("detect", lambda state: detect_patterns(state, llm))
    workflow.add_node("assess", lambda state: assess_input(state))
    workflow.add_node("analyze", lambda state: analyze_narrative(state, llm))
    workflow.add_node("respond", lambda state: {"next": "detect"})
    workflow.add_node("error", lambda state: {"next": "end"})
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "detect",
        lambda state: state.get("next", "assess")
    )
    
    workflow.add_conditional_edges(
        "assess",
        lambda state: state.get("next", "analyze")
    )
    
    workflow.add_conditional_edges(
        "analyze",
        lambda state: state.get("next", "respond")
    )
    
    workflow.add_conditional_edges(
        "respond",
        lambda state: state.get("next", "detect")
    )
    
    workflow.add_edge("error", "end")
    
    # Set entry point
    workflow.set_entry_point("detect")
    
    return workflow.compile()
