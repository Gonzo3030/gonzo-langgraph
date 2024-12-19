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

# Node Wrappers

def ensure_unified_state(state: Union[Dict, UnifiedState]) -> UnifiedState:
    """Ensure we have a UnifiedState object."""
    if isinstance(state, UnifiedState):
        return state
    return UnifiedState(**state)

def market_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle market monitoring stage"""
    # Ensure we have a UnifiedState
    state = ensure_unified_state(state)
    
    try:
        # Market monitoring logic here
        # ...
        
        # Move to news monitoring next
        state.current_stage = WorkflowStage.NEWS_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Market monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
        
    return state.model_dump()

def news_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle news monitoring stage"""
    state = ensure_unified_state(state)
    
    try:
        # Only update news every 5 cycles
        cycle_count = len(state.messages) # Simple way to track cycles
        if cycle_count % GRAPH_CONFIG["news_cycle"] == 0:
            monitor = NewsMonitor()
            # Note: We'll need to handle the async call differently
            if state.narrative.pending_analyses:
                state.current_stage = WorkflowStage.PATTERN_ANALYSIS
                return state.model_dump()
        
        # Move to social monitoring
        state.current_stage = WorkflowStage.SOCIAL_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"News monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
        
    return state.model_dump()

def social_monitor_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle social monitoring stage"""
    state = ensure_unified_state(state)
    
    try:
        # Check rate limits before proceeding
        if state.x_integration.rate_limits["remaining"] <= 1:
            if state.x_integration.rate_limits["reset_time"] > datetime.now():
                # Skip social monitoring this cycle
                state.current_stage = WorkflowStage.PATTERN_ANALYSIS
                return state.model_dump()
        
        # Social monitoring logic here
        # ...
        
        state.current_stage = WorkflowStage.PATTERN_ANALYSIS
        
    except Exception as e:
        state.api_errors.append(f"Social monitoring error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
        
    return state.model_dump()

def pattern_analysis_node(state: Union[Dict, UnifiedState], llm: Any) -> Dict[str, Any]:
    """Handle pattern analysis stage"""
    state = ensure_unified_state(state)
    
    try:
        # Update context with news data
        context = {
            "market_events": state.narrative.market_events,
            "social_events": state.narrative.social_events,
            "news_events": state.narrative.news_events,
            "patterns": state.analysis.market_patterns +
                      state.analysis.social_patterns +
                      state.analysis.news_patterns
        }
        
        # Note: We'll need to handle the async call differently
        patterns = {}
        
        # Update state with detected patterns
        if patterns:
            state.analysis.market_patterns.extend(patterns.get('market_patterns', []))
            state.analysis.social_patterns.extend(patterns.get('social_patterns', []))
            state.analysis.news_patterns.extend(patterns.get('news_patterns', []))
            state.analysis.correlations.extend(patterns.get('correlations', []))
        
        # Calculate significance
        total_patterns = len(state.analysis.market_patterns) + \
                        len(state.analysis.social_patterns) + \
                        len(state.analysis.news_patterns)
        
        if total_patterns > 0:
            state.current_stage = WorkflowStage.NARRATIVE_GENERATION
        else:
            state.current_stage = WorkflowStage.MARKET_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Pattern analysis error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
        
    return state.model_dump()

def narrative_generation_node(state: Union[Dict, UnifiedState], llm: Any) -> Dict[str, Any]:
    """Handle narrative generation stage"""
    state = ensure_unified_state(state)
    
    try:
        # Update context with news data
        context = {
            "messages": state.messages,
            "market_events": state.narrative.market_events,
            "social_events": state.narrative.social_events,
            "news_events": state.narrative.news_events,
            "patterns": {
                "market": state.analysis.market_patterns,
                "social": state.analysis.social_patterns,
                "news": state.analysis.news_patterns,
                "correlations": state.analysis.correlations
            }
        }
        
        # Note: We'll need to handle the async call differently
        response = None
        
        if response and response.get('significance', 0) > 0.7:
            state.x_integration.queued_posts.append(response.get('content', ''))
            state.current_stage = WorkflowStage.RESPONSE_POSTING
        else:
            state.current_stage = WorkflowStage.MARKET_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Narrative generation error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
        
    return state.model_dump()

def response_posting_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle response posting stage"""
    state = ensure_unified_state(state)
    
    try:
        # Response posting logic here
        # ...
        
        state.current_stage = WorkflowStage.MARKET_MONITORING
        
    except Exception as e:
        state.api_errors.append(f"Response posting error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
        
    return state.model_dump()

def error_recovery_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle error recovery stage"""
    state = ensure_unified_state(state)
    
    try:
        # Log errors
        for error in state.api_errors:
            state.add_message(f"Error encountered: {error}", source="error")
        
        # Clear errors after logging
        state.api_errors.clear()
        
        # Return to market monitoring
        state.current_stage = WorkflowStage.MARKET_MONITORING
        return state.model_dump()
        
    except Exception as e:
        # If error recovery fails, end the workflow
        state.add_message(f"Critical error in recovery: {str(e)}", source="critical")
        return {"type": "end"}

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
    
    # Add error recovery
    workflow.add_node("error_recovery", error_recovery_node)
    
    # Add conditional edges based on WorkflowStage
    def get_stage(x: Union[Dict, UnifiedState]) -> str:
        state = ensure_unified_state(x)
        return state.current_stage.value
    
    workflow.add_conditional_edges(
        "market_monitor",
        get_stage,
        {
            WorkflowStage.NEWS_MONITORING.value: "news_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "news_monitor",
        get_stage,
        {
            WorkflowStage.SOCIAL_MONITORING.value: "social_monitor",
            WorkflowStage.PATTERN_ANALYSIS.value: "pattern_analysis",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "social_monitor",
        get_stage,
        {
            WorkflowStage.PATTERN_ANALYSIS.value: "pattern_analysis",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "pattern_analysis",
        get_stage,
        {
            WorkflowStage.NARRATIVE_GENERATION.value: "narrative_generation",
            WorkflowStage.MARKET_MONITORING.value: "market_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "narrative_generation",
        get_stage,
        {
            WorkflowStage.RESPONSE_POSTING.value: "response_posting",
            WorkflowStage.MARKET_MONITORING.value: "market_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "response_posting",
        get_stage,
        {
            WorkflowStage.MARKET_MONITORING.value: "market_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "error_recovery",
        get_stage,
        {
            WorkflowStage.MARKET_MONITORING.value: "market_monitor",
            END: END
        }
    )
    
    # Set entry point
    workflow.set_entry_point("market_monitor")
    
    # Compile with config
    final_config = {**GRAPH_CONFIG}
    if config:
        final_config.update(config)
        
    return workflow.compile()

def initialize_workflow() -> Dict[str, Any]:
    """Initialize the workflow with a clean state"""
    initial_state = create_initial_state()
    
    # Set initial stage
    initial_state.current_stage = WorkflowStage.MARKET_MONITORING
    
    # Add system prompt to messages
    initial_state.add_message(
        SYSTEM_PROMPT,
        source="system"
    )
    
    return initial_state.model_dump()