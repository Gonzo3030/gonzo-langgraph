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
    
    # Add all conditional edges
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
    
    workflow.add_conditional_edges(
        "response_posting",
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
    
    # Set entrypoint
    workflow.set_entry_point("market_monitor")
    
    return workflow