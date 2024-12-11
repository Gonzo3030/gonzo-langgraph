from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState, NextStep
from .nodes.x_nodes import XNodes
from .nodes.rag_nodes import RAGNodes
from ..state.x_state import XState, MonitoringState

StateType = TypeVar("StateType", bound=BaseModel)

# Initialize components
x_nodes = XNodes()
rag_nodes = RAGNodes()

async def handle_content_monitor(state: GonzoState) -> Dict[str, Any]:
    """Content monitoring node handler."""
    # Ensure X state exists
    if not hasattr(state, 'x_state'):
        state.x_state = XState()
    if not hasattr(state, 'monitoring_state'):
        state.monitoring_state = MonitoringState()
    
    # Run content monitoring
    state_dict = state.dict()
    updated_state = await x_nodes.monitor_content(state_dict)
    
    # Update state with monitoring results
    state.x_state = updated_state['x_state']
    if 'new_content' in updated_state:
        state.discovered_content = updated_state['new_content']
        state.next_step = NextStep.RAG  # Proceed to RAG analysis
    else:
        state.next_step = NextStep.QUEUE  # No new content, check queues
    
    return {"state": state}

async def handle_rag_analysis(state: GonzoState) -> Dict[str, Any]:
    """RAG analysis node handler."""
    # Run RAG analysis on discovered content
    updated_state = await rag_nodes.analyze_content(state)
    
    # Move to next step
    state = updated_state['state']
    state.next_step = NextStep.ASSESSMENT
    
    return {"state": state}

async def handle_assessment(state: GonzoState) -> Dict[str, Any]:
    """Assessment node handler."""
    # Use RAG analysis results to determine response strategy
    state.next_step = NextStep.QUEUE
    return {"state": state}

async def handle_queue_processing(state: GonzoState) -> Dict[str, Any]:
    """Queue processing node handler."""
    if not hasattr(state, 'x_state'):
        state.x_state = XState()
    
    # Process queues
    state_dict = state.dict()
    updated_state = await x_nodes.process_queues(state_dict)
    
    # Update state with queue results
    state.x_state = updated_state['x_state']
    if 'posted_content' in updated_state:
        state.posted_content = updated_state['posted_content']
    if 'interactions' in updated_state:
        state.interactions = updated_state['interactions']
    
    # Back to monitoring
    state.next_step = NextStep.MONITOR
    
    return {"state": state}

def router(state: GonzoState) -> str:
    """Router node for the workflow."""
    if not state.next_step:
        state.next_step = NextStep.MONITOR
    
    next_steps = {
        NextStep.MONITOR: "content_monitor",
        NextStep.RAG: "rag_analysis",
        NextStep.ASSESSMENT: "assessment",
        NextStep.QUEUE: "queue_processing",
        NextStep.END: "end"
    }
    
    return next_steps.get(state.next_step, "end")

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
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