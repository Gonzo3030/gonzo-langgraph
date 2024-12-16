"""Main workflow definition for Gonzo."""

import os
from typing import Dict, Any, Callable
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
import asyncio

from .types import GonzoState
from .nodes.pattern_detection import detect_patterns
from .nodes.assessment import assess_input
from .nodes.narrative import analyze_narrative
from .nodes.x_posting import post_to_x
from .config import ANTHROPIC_MODEL, RATE_LIMIT_DELAY

def sync_wrapper(async_func):
    """Wrapper to run async functions in sync context."""
    def wrapper(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return wrapper

def create_node_fn(func: Callable, llm: Any = None) -> Callable:
    """Create a node function that includes the LLM if needed."""
    if llm:
        return lambda state: func(state, llm)
    return lambda state: func(state)

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Initialize LLM
    llm = ChatAnthropic(
        model=ANTHROPIC_MODEL,
        temperature=0.7,
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )
    
    # Add nodes with sync wrappers
    workflow.add_node(
        "detect", 
        sync_wrapper(create_node_fn(detect_patterns, llm))
    )
    
    workflow.add_node(
        "assess", 
        sync_wrapper(create_node_fn(assess_input, llm))
    )
    
    workflow.add_node(
        "analyze", 
        sync_wrapper(create_node_fn(analyze_narrative, llm))
    )
    
    workflow.add_node(
        "x_post",
        sync_wrapper(create_node_fn(post_to_x))
    )
    
    workflow.add_node(
        "respond",
        lambda state: {
            "timestamp": state.timestamp,
            "next": "detect" if not state.response.queued_responses else "x_post"
        }
    )
    
    workflow.add_node(
        "error",
        lambda state: {"timestamp": state.timestamp, "next": END}
    )
    
    # Add edges with branching logic
    workflow.add_conditional_edges(
        "detect",
        lambda state: {
            "assess": 0.8,  # Most likely path
            "analyze": 0.2  # Direct to analysis if strong pattern detected
        }.get(state.next, "assess")
    )
    
    workflow.add_conditional_edges(
        "assess",
        lambda state: state.next
    )
    
    workflow.add_conditional_edges(
        "analyze",
        lambda state: "respond"
    )
    
    workflow.add_conditional_edges(
        "respond",
        lambda state: "x_post" if state.response.queued_responses else "detect"
    )
    
    workflow.add_conditional_edges(
        "x_post",
        lambda state: state.next
    )
    
    workflow.add_edge("error", END)
    
    # Set entry point
    workflow.set_entry_point("detect")
    
    return workflow.compile()