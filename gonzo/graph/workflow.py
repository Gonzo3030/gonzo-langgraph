from typing import Dict, Any, TypeVar, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState, NextStep
from .nodes.x_nodes import XNodes
from ..state.x_state import XState, MonitoringState

StateType = TypeVar("StateType", bound=BaseModel)

# Initialize X components
x_nodes = XNodes()

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
        state.new_content = updated_state['new_content']
    
    return {"state": state}

async def handle_assessment(state: GonzoState) -> Dict[str, Any]:
    """Assessment node handler."""
    # Implement assessment logic here
    return {"state": state}

async def handle_narrative(state: GonzoState) -> Dict[str, Any]:
    """Narrative analysis handler."""
    # Implement narrative analysis logic here
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
    
    return {"state": state}

def router(state: GonzoState) -> str:
    """Router node for the workflow."""
    if not state.next_step:
        state.next_step = NextStep.MONITOR
    
    next_steps = {
        NextStep.MONITOR: "content_monitor",
        NextStep.ASSESSMENT: "assessment",
        NextStep.NARRATIVE: "narrative",
        NextStep.QUEUE: "queue_processing",
        NextStep.END: "end"
    }
    
    return next_steps.get(state.next_step, "end")

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes with their respective handlers
    workflow.add_node("start", lambda x: {"state": x})
    workflow.add_node("content_monitor", handle_content_monitor)
    workflow.add_node("assessment", handle_assessment)
    workflow.add_node("narrative", handle_narrative)
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
            "assessment": "assessment",
            "queue_processing": "queue_processing",
            "end": "end"
        }
    )
    
    workflow.add_conditional_edges(
        "assessment",
        router,
        {
            "narrative": "narrative",
            "queue_processing": "queue_processing",
            "end": "end"
        }
    )
    
    workflow.add_conditional_edges(
        "narrative",
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