"""Main workflow definition for Gonzo."""

from typing import Dict, Any
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

from .types import GonzoState, NextStep
from .nodes.pattern_detection import detect_patterns
from .nodes.assessment import assess_content
from .nodes.narrative import process_narrative

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Initialize LLM
    llm = ChatOpenAI()
    
    # Add nodes
    workflow.add_node("pattern_detection", lambda state: detect_patterns(state, llm))
    workflow.add_node("assessment", lambda state: assess_content(state, llm))
    workflow.add_node("narrative", lambda state: process_narrative(state, llm))
    
    # Define edges based on next_step
    workflow.add_edge("pattern_detection", condition_fn)
    workflow.add_edge("assessment", condition_fn)
    workflow.add_edge("narrative", condition_fn)
    
    # Set entry point
    workflow.set_entry_point("pattern_detection")
    
    return workflow.compile()

def condition_fn(state: GonzoState) -> str:
    """Determine next step based on state."""
    return state.next_step or NextStep.END
