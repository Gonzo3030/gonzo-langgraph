"""Main workflow definition for Gonzo."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
import asyncio

from .types import GonzoState, NextStep
from .nodes.pattern_detection import detect_patterns
from .nodes.assessment import assess_input
from .nodes.narrative import analyze_narrative
from .config import ANTHROPIC_MODEL

def sync_wrapper(async_func):
    """Wrapper to run async functions in sync context."""
    def wrapper(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return wrapper

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Initialize LLM
    llm = ChatAnthropic(
        model=ANTHROPIC_MODEL,
        temperature=0.7
    )
    
    # Add nodes with sync wrappers
    workflow.add_node(
        "detect",
        sync_wrapper(lambda state: detect_patterns(state, llm)),
        ['analysis', 'memory', 'timestamp']
    )
    
    workflow.add_node(
        "assess",
        sync_wrapper(lambda state: assess_input(state)),
        ['analysis', 'memory', 'timestamp']
    )
    
    workflow.add_node(
        "analyze",
        sync_wrapper(lambda state: analyze_narrative(state, llm)),
        ['response', 'memory', 'timestamp']
    )
    
    workflow.add_node(
        "respond",
        lambda state: {"next": "detect", "timestamp": state.timestamp},
        ['timestamp']
    )
    
    workflow.add_node(
        "error",
        lambda state: {"next": END, "timestamp": state.timestamp},
        ['timestamp']
    )
    
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
    
    workflow.add_edge("error", END)
    
    # Set entry point
    workflow.set_entry_point("detect")
    
    return workflow.compile()