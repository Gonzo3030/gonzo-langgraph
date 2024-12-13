"""Core workflow definition for Gonzo system."""

from typing import Dict, Any, TypeVar, Annotated, Optional
from langchain_core.language_models import BaseLLM
from langgraph.graph import StateGraph, END

from ..config import MODEL_CONFIG, GRAPH_CONFIG
from ..types import GonzoState
from ..nodes.initial_assessment import initial_assessment
from ..nodes.pattern_detection import detect_patterns
from ..nodes.response_generation import generate_response

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
    workflow.add_node("assess", lambda x: initial_assessment(x["state"], llm))
    workflow.add_node("detect_patterns", lambda x: detect_patterns(x["state"], llm))
    workflow.add_node("generate_response", lambda x: generate_response(x["state"], llm))
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
        lambda x: "next" in x and x["next"] != "error",
        {
            True: "detect_patterns",
            False: "end"
        }
    )
    
    workflow.add_conditional_edges(
        "detect_patterns",
        lambda x: x["state"].analysis.significance > 0.5,
        {
            True: "generate_response",
            False: "end"
        }
    )
    
    workflow.add_edge("generate_response", "end")
    
    # Compile with config
    final_config = {**GRAPH_CONFIG}
    if config:
        final_config.update(config)
        
    return workflow.compile()