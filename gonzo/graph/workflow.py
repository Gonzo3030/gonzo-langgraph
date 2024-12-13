"""Core workflow definition for Gonzo system."""

from typing import Dict, Any, TypeVar, Annotated, Optional
from langchain_core.language_models import BaseLLM
from langgraph.graph import StateGraph, END

from ..config import MODEL_CONFIG, GRAPH_CONFIG
from ..types import GonzoState
from .nodes import initial_assessment, analyze_patterns, generate_response

def create_workflow(
    llm: Optional[BaseLLM] = None,
    config: Optional[Dict[str, Any]] = None
) -> StateGraph:
    """Create the main workflow graph.
    
    Args:
        llm: Optional language model override
        config: Optional configuration override
        
    Returns:
        Compiled workflow graph
    """
    # Initialize graph with state type
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("start", lambda x: {"state": x})
    workflow.add_node("assess", initial_assessment)
    workflow.add_node("analyze", analyze_patterns)
    workflow.add_node("respond", generate_response)
    workflow.add_node("end", lambda x: {"state": x})
    
    # Set entry point
    workflow.set_entry_point("start")
    
    # Add edges with conditional routing
    workflow.add_conditional_edges(
        "start",
        lambda x: x["state"].messages.current_message is not None,
        {
            True: "assess",
            False: "end"
        }
    )
    
    workflow.add_conditional_edges(
        "assess",
        lambda x: len(x["state"].analysis.patterns) > 0,
        {
            True: "analyze",
            False: "end"
        }
    )
    
    workflow.add_conditional_edges(
        "analyze",
        lambda x: x["state"].analysis.significance > 0.5,
        {
            True: "respond",
            False: "end"
        }
    )
    
    workflow.add_edge("respond", "end")
    
    # Compile with config
    final_config = {**GRAPH_CONFIG}
    if config:
        final_config.update(config)
        
    return workflow.compile()