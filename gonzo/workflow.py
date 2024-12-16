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
    # Initialize the graph with updatable fields
    workflow = StateGraph(GonzoState)
    
    # Initialize LLM
    llm = ChatAnthropic(
        model=ANTHROPIC_MODEL,
        temperature=0.7
    )
    
    # Add nodes with sync wrappers
    workflow.add_node("detect", sync_wrapper(lambda state: detect_patterns(state, llm)))
    workflow.add_node("assess", sync_wrapper(lambda state: assess_input(state)))
    workflow.add_node("analyze", sync_wrapper(lambda state: analyze_narrative(state, llm)))
    workflow.add_node("respond", lambda state: {"timestamp": state.timestamp, "next": "detect"})
    workflow.add_node("error", lambda state: {"timestamp": state.timestamp, "next": END})
    
    # Add conditional edges with fixed routing
    workflow.add_edge("detect", "assess")
    workflow.add_edge("assess", "analyze")
    workflow.add_edge("analyze", "respond")
    workflow.add_edge("respond", "detect")
    workflow.add_edge("error", END)
    
    # Set entry point
    workflow.set_entry_point("detect")
    
    return workflow.compile()