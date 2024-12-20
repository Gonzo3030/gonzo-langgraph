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
    """Ensure we're working with a UnifiedState instance."""
    if isinstance(state, dict):
        return UnifiedState(**state)
    return state

def market_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle market monitoring phase."""
    state = ensure_unified_state(state)
    
    try:
        # Perform market monitoring
        initial_assessment(state)
        
        # Determine next stage based on results
        if state.narrative.pending_analyses:
            state.current_stage = WorkflowStage.NEWS_MONITORING
        else:
            state.current_stage = WorkflowStage.CYCLE_COMPLETE
            
    except Exception as e:
        state.api_errors.append(f"Market monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def news_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle news monitoring phase."""
    state = ensure_unified_state(state)
    
    try:
        # Initialize news monitor if needed
        news_monitor = NewsMonitor()
        
        # Update state with news data
        state = news_monitor.update_news_state(state)
        
        # Determine next stage
        if state.narrative.pending_analyses:
            state.current_stage = WorkflowStage.SOCIAL_MONITORING
        else:
            state.current_stage = WorkflowStage.CYCLE_COMPLETE
            
    except Exception as e:
        state.api_errors.append(f"News monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def social_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle social monitoring phase."""
    state = ensure_unified_state(state)
    
    try:
        # Check rate limits first
        if state.x_integration.rate_limits["remaining"] <= 1:
            state.add_message("Rate limit reached, skipping social monitoring", source="system")
            state.current_stage = WorkflowStage.PATTERN_ANALYSIS
            return state.model_dump()
        
        # Perform social monitoring
        # [Your social monitoring logic here]
        
        # Move to pattern analysis if we have data
        if state.narrative.pending_analyses:
            state.current_stage = WorkflowStage.PATTERN_ANALYSIS
        else:
            state.current_stage = WorkflowStage.CYCLE_COMPLETE
            
    except Exception as e:
        state.api_errors.append(f"Social monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def pattern_analysis_node(state: Union[Dict, UnifiedState], llm: BaseLLM) -> Dict[str, Any]:
    """Handle pattern analysis phase."""
    state = ensure_unified_state(state)
    
    try:
        # Detect patterns
        detect_patterns(state)
        
        # Move to narrative generation if patterns found
        if state.narrative.patterns:
            state.current_stage = WorkflowStage.NARRATIVE_GENERATION
        else:
            state.current_stage = WorkflowStage.CYCLE_COMPLETE
            
    except Exception as e:
        state.api_errors.append(f"Pattern analysis error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def narrative_generation_node(state: Union[Dict, UnifiedState], llm: BaseLLM) -> Dict[str, Any]:
    """Handle narrative generation phase."""
    state = ensure_unified_state(state)
    
    try:
        # Generate response
        response = generate_response(state, llm)
        
        if response and response.significance > 0.7:
            state.current_stage = WorkflowStage.RESPONSE_POSTING
        else:
            state.current_stage = WorkflowStage.CYCLE_COMPLETE
            
    except Exception as e:
        state.api_errors.append(f"Narrative generation error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def response_posting_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle response posting phase."""
    state = ensure_unified_state(state)
    
    try:
        # [Your response posting logic here]
        
        # Move to cycle completion
        state.current_stage = WorkflowStage.CYCLE_COMPLETE
        
    except Exception as e:
        state.api_errors.append(f"Response posting error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def error_recovery_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle error recovery."""
    state = ensure_unified_state(state)
    
    try:
        # Log error state
        state.add_message("Entering error recovery", source="system")
        
        # Check error severity
        if len(state.api_errors) > GRAPH_CONFIG["error_threshold"]:
            state.current_stage = WorkflowStage.SHUTDOWN
        else:
            state.current_stage = WorkflowStage.CYCLE_COMPLETE
            
    except Exception as e:
        # If error recovery fails, shut down
        state.current_stage = WorkflowStage.SHUTDOWN
    
    return state.model_dump()

def cycle_complete_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle cycle completion."""
    state = ensure_unified_state(state)
    
    try:
        # Log cycle completion
        state.add_message("Cycle complete", source="system")
        
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
        state.add_message("Shutting down Gonzo...", source="system")
        return END
        
    except Exception as e:
        # Even if logging fails, we need to end
        return END

def create_workflow(
    llm: Optional[BaseLLM] = None,
    config: Optional[Dict[str, Any]] = None
) -> StateGraph:
    """Create the main workflow graph using unified state management."""
    # Initialize graph with unified state
    workflow = StateGraph(UnifiedState)
    
    # Add monitoring nodes
    workflow.add_node("market_monitor", market_monitor_node)
    workflow.add_node("news_monitor", news_monitor_node)
    workflow.add_node("social_monitor", social_monitor_node)
    
    # Add analysis and generation nodes
    workflow.add_node("pattern_analysis", 
                     lambda x: pattern_analysis_node(x, llm))
    workflow.add_node("narrative_generation", 
                     lambda x: narrative_generation_node(x, llm))
    workflow.add_node("response_posting", response_posting_node)
    
    # Add cycle control nodes
    workflow.add_node("cycle_complete", cycle_complete_node)
    workflow.add_node("shutdown", shutdown_node)
    workflow.add_node("error_recovery", error_recovery_node)
    
    # Add conditional edges based on WorkflowStage
    def get_stage(x: Union[Dict, UnifiedState]) -> str:
        state = ensure_unified_state(x)
        return state.current_stage.value
    
    # Market monitoring edges
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
    
    # News monitoring edges
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
    
    # Social monitoring edges
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
    
    # Shutdown edges should end the workflow
    workflow.add_conditional_edges(
        "shutdown",
        get_stage,
        {END: END}
    )
    
    # Set entry point
    workflow.set_entry_point("market_monitor")
    
    # Set configuration
    final_config = GRAPH_CONFIG.copy()
    if config:
        final_config.update(config)
    
    return workflow.compile()