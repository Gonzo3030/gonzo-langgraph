"""Core workflow definition for Gonzo system."""
from typing import Dict, Any, Optional, Union
from datetime import datetime
from langchain_core.language_models import BaseLLM
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from functools import partial
from operator import itemgetter

from ..config import MODEL_CONFIG, GRAPH_CONFIG, SYSTEM_PROMPT
from ..state_management import (
    UnifiedState,
    WorkflowStage,
    create_initial_state
)
from ..nodes.initial_assessment import initial_assessment
from ..nodes.pattern_detection import detect_patterns
from ..nodes.response_generation import generate_response
from ..monitoring.news_monitor import NewsMonitor

def ensure_unified_state(state: Union[Dict, UnifiedState]) -> UnifiedState:
    """Ensure we're working with a UnifiedState object."""
    if isinstance(state, dict):
        return UnifiedState(**state)
    return state

def market_monitor_node(state: Dict) -> Dict[str, Any]:
    """Handle market monitoring stage."""
    # Convert input state
    if isinstance(state, dict) and "state" in state:
        state = state["state"]
    state = ensure_unified_state(state)
    
    try:
        # Force transition to next stage
        state.current_stage = WorkflowStage.NEWS_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Market monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return {"state": state.model_dump()}

def news_monitor_node(state: Dict) -> Dict[str, Any]:
    """Handle news monitoring stage."""
    # Convert input state
    if isinstance(state, dict) and "state" in state:
        state = state["state"]
    state = ensure_unified_state(state)
    
    try:
        # Force transition to next stage
        state.current_stage = WorkflowStage.CYCLE_COMPLETE
        
    except Exception as e:
        state.api_errors.append(f"News monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return {"state": state.model_dump()}

def cycle_complete_node(state: Dict) -> Dict[str, Any]:
    """Handle cycle completion."""
    # Convert input state
    if isinstance(state, dict) and "state" in state:
        state = state["state"]
    state = ensure_unified_state(state)
    
    try:
        # Log cycle completion
        state.messages.append("Cycle complete")
        
        # Reset for next cycle
        state.narrative.pending_analyses = False
        state.narrative.market_events.clear()
        state.narrative.social_events.clear()
        state.narrative.news_events.clear()
        
        # Check cycle count
        state.cycle_count = getattr(state, 'cycle_count', 0) + 1
        
        if state.cycle_count >= 3:  # For testing, limit to 3 cycles
            state.current_stage = WorkflowStage.SHUTDOWN
        else:
            # Move back to market monitoring for next cycle
            state.current_stage = WorkflowStage.MARKET_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Cycle completion error: {str(e)}")
        state.current_stage = WorkflowStage.SHUTDOWN
    
    return {"state": state.model_dump()}

def error_recovery_node(state: Dict) -> Dict[str, Any]:
    """Handle error recovery."""
    # Convert input state
    if isinstance(state, dict) and "state" in state:
        state = state["state"]
    state = ensure_unified_state(state)
    
    try:
        # Log errors
        for error in state.api_errors:
            state.messages.append(f"Error encountered: {error}")
        
        # Clear error list after logging
        state.api_errors.clear()
        
        # Move to cycle completion
        state.current_stage = WorkflowStage.CYCLE_COMPLETE
        
    except Exception as e:
        # If error recovery itself fails, we need to shut down
        state.messages.append(f"Critical error in recovery: {str(e)}")
        state.current_stage = WorkflowStage.SHUTDOWN
    
    return {"state": state.model_dump()}

def shutdown_node(state: Dict) -> Dict[str, Any]:
    """Handle graceful shutdown."""
    # Convert input state
    if isinstance(state, dict) and "state" in state:
        state = state["state"]
    state = ensure_unified_state(state)
    
    state.messages.append("Shutting down Gonzo...")
    return {"state": state.model_dump(), "end": True}

def create_workflow(
    llm: Optional[BaseLLM] = None,
    config: Optional[Dict[str, Any]] = None
) -> StateGraph:
    """Create the main workflow graph."""
    # Create graph with config
    config = config or {}
    config['recursion_limit'] = config.get('recursion_limit', 100)
    
    workflow = StateGraph(
        UnifiedState,
        config
    )
    
    # Add nodes
    workflow.add_node("market_monitor", market_monitor_node)
    workflow.add_node("news_monitor", news_monitor_node)
    workflow.add_node("cycle_complete", cycle_complete_node)
    workflow.add_node("error_recovery", error_recovery_node)
    workflow.add_node("shutdown", shutdown_node)
    
    # Add edges
    def get_stage(x: Dict) -> str:
        # Extract state from wrapper if needed
        if isinstance(x, dict) and "state" in x:
            state = ensure_unified_state(x["state"])
        else:
            state = ensure_unified_state(x)
        return state.current_stage.value
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "market_monitor",
        get_stage,
        {
            WorkflowStage.NEWS_MONITORING.value: "news_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery",
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    workflow.add_conditional_edges(
        "news_monitor",
        get_stage,
        {
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery",
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    workflow.add_conditional_edges(
        "error_recovery",
        get_stage,
        {
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    workflow.add_conditional_edges(
        "cycle_complete",
        get_stage,
        {
            WorkflowStage.MARKET_MONITORING.value: "market_monitor",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    # Set entry point
    workflow.set_entry_point("market_monitor")
    
    return workflow