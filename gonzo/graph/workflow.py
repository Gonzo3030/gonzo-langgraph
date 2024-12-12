from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState, NextStep
from .nodes.x_nodes import XNodes
from .nodes.rag_nodes import RAGNodes
from ..state.x_state import XState, MonitoringState

StateType = TypeVar("StateType", bound=BaseModel)

def create_workflow(test_mode: bool = False) -> StateGraph:
    """Create the main Gonzo workflow graph.
    
    Args:
        test_mode: Whether to run in test mode
    """
    # Initialize components
    x_nodes = XNodes()
    rag_nodes = RAGNodes(test_mode=test_mode)
    
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("start", lambda x: {"state": x})
    workflow.add_node("content_monitor", handle_content_monitor)
    workflow.add_node("rag_analysis", handle_rag_analysis)
    workflow.add_node("assessment", handle_assessment)
    workflow.add_node("queue_processing", handle_queue_processing)
    workflow.add_node("end", lambda x: {"state": x})
    
    # Set up the entry point
    workflow.set_entry_point("start")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "start",
        lambda x: "content_monitor",
        {"content_monitor": "content_monitor"}
    )
    
    workflow.add_conditional_edges(
        "content_monitor",
        router,
        {
            "rag_analysis": "rag_analysis",
            "queue_processing": "queue_processing",
            "end": "end"
        }
    )
    
    workflow.add_conditional_edges(
        "rag_analysis",
        router,
        {
            "assessment": "assessment",
            "queue_processing": "queue_processing",
            "end": "end"
        }
    )
    
    workflow.add_conditional_edges(
        "assessment",
        router,
        {
            "queue_processing": "queue_processing",
            "end": "end"
        }
    )
    
    workflow.add_conditional_edges(
        "queue_processing",
        router,
        {
            "content_monitor": "content_monitor",
            "end": "end"
        }
    )
    
    return workflow.compile()