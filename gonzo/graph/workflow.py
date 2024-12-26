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

# Node Definitions
def market_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle market monitoring stage."""
    state = ensure_unified_state(state)
    
    try:
        # Force transition to next stage after market monitoring
        state.current_stage = WorkflowStage.NEWS_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Market monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def news_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle news monitoring stage."""
    state = ensure_unified_state(state)
    
    try:
        # Force transition to next stage
        state.current_stage = WorkflowStage.SOCIAL_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"News monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def social_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle social media monitoring stage."""
    state = ensure_unified_state(state)
    
    try:
        # Force transition to next stage
        state.current_stage = WorkflowStage.PATTERN_ANALYSIS
        
    except Exception as e:
        state.api_errors.append(f"Social monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def pattern_analysis_node(state: Union[Dict, UnifiedState], llm: BaseLLM) -> Dict[str, Any]:
    """Handle pattern analysis stage."""
    state = ensure_unified_state(state)
    
    try:
        # Force to cycle complete for now
        state.current_stage = WorkflowStage.CYCLE_COMPLETE
        
    except Exception as e:
        state.api_errors.append(f"Pattern analysis error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def narrative_generation_node(state: Union[Dict, UnifiedState], llm: BaseLLM) -> Dict[str, Any]:
    """Handle narrative generation stage."""
    state = ensure_unified_state(state)
    
    try:
        # Force to response posting
        state.current_stage = WorkflowStage.RESPONSE_POSTING
        
    except Exception as e:
        state.api_errors.append(f"Narrative generation error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def response_posting_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle response posting stage."""
    state = ensure_unified_state(state)
    
    try:
        state.current_stage = WorkflowStage.CYCLE_COMPLETE
        
    except Exception as e:
        state.api_errors.append(f"Response posting error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
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

def create_workflow(
    llm: Optional[BaseLLM] = None,
    config: Optional[Dict[str, Any]] = None
) -> StateGraph:
    """Create the main workflow graph."""
    workflow = StateGraph(UnifiedState)
    
    # Add nodes
    workflow.add_node("market_monitor", market_monitor_node)
    workflow.add_node("news_monitor", news_monitor_node)
    workflow.add_node("social_monitor", social_monitor_node)
    
    workflow.add_node("pattern_analysis", 
                     lambda x: pattern_analysis_node(x, llm))
    workflow.add_node("narrative_generation", 
                     lambda x: narrative_generation_node(x, llm))
    workflow.add_node("response_posting", response_posting_node)
    
    workflow.add_node("cycle_complete", cycle_complete_node)
    workflow.add_node("error_recovery", error_recovery_node)
    workflow.add_node("shutdown", shutdown_node)
    
    # Add edges
    def get_stage(x: Union[Dict, UnifiedState]) -> str:
        state = ensure_unified_state(x)
        return state.current_stage.value
    
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
            WorkflowStage.SOCIAL_MONITORING.value: "social_monitor",
            WorkflowStage.PATTERN_ANALYSIS.value: "pattern_analysis",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery",
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    workflow.add_conditional_edges(
        "social_monitor",
        get_stage,
        {
            WorkflowStage.PATTERN_ANALYSIS.value: "pattern_analysis",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery",
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    # Pattern analysis edges
    workflow.add_conditional_edges(
        "pattern_analysis",
        get_stage,
        {
            WorkflowStage.NARRATIVE_GENERATION.value: "narrative_generation",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery",
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    # Narrative generation edges
    workflow.add_conditional_edges(
        "narrative_generation",
        get_stage,
        {
            WorkflowStage.RESPONSE_POSTING.value: "response_posting",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery",
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    # Response posting edges
    workflow.add_conditional_edges(
        "response_posting",
        get_stage,
        {
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery",
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    # Error recovery edges
    workflow.add_conditional_edges(
        "error_recovery",
        get_stage,
        {
            WorkflowStage.CYCLE_COMPLETE.value: "cycle_complete",
            WorkflowStage.SHUTDOWN.value: "shutdown"
        }
    )
    
    # Cycle complete edges
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