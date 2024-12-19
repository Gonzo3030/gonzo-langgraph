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

# Node Wrappers and Helper Functions
[... previous node functions remain the same ...]

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
    
    # Shutdown edges
    workflow.add_conditional_edges(
        "shutdown",
        get_stage,
        {END: END}
    )
    
    # Set entry point
    workflow.set_entry_point("market_monitor")
    
    # Set configuration
    final_config = {
        "recursion_limit": GRAPH_CONFIG.get("recursion_limit", 100),
        "cycle_timeout": GRAPH_CONFIG.get("cycle_timeout", 300)
    }
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