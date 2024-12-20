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

[... previous code remains the same ...]

# Utility nodes
def error_recovery_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle error recovery."""
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
    
    return state.model_dump()

def cycle_complete_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle cycle completion."""
    state = ensure_unified_state(state)
    
    try:
        # Log cycle completion
        state.messages.append("Cycle complete")
        
        # Reset for next cycle
        state.narrative.pending_analyses = False
        state.narrative.market_events.clear()
        state.narrative.social_events.clear()
        state.narrative.news_events.clear()
        
        # Move back to market monitoring for next cycle
        state.current_stage = WorkflowStage.MARKET_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Cycle completion error: {str(e)}")
        state.current_stage = WorkflowStage.SHUTDOWN
    
    return state.model_dump()

def shutdown_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle graceful shutdown."""
    state = ensure_unified_state(state)
    
    try:
        # Log shutdown
        state.messages.append("Shutting down Gonzo...")
        return END
        
    except Exception as e:
        # Even if logging fails, we need to end
        return END