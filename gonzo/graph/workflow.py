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

def market_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle market monitoring stage."""
    state = ensure_unified_state(state)
    
    try:
        # Process market data
        if state.market_data:
            state.narrative.market_events.extend(
                [event for event in state.market_data.values() 
                 if event.significance > GRAPH_CONFIG['market_significance_threshold']]
            )
            
            if state.narrative.market_events:
                state.narrative.pending_analyses = True
        
        # Transition to next stage
        state.current_stage = WorkflowStage.NEWS_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Market monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()
