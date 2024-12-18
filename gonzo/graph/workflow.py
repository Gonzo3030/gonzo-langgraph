"""Core workflow definition for Gonzo system."""

from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.language_models import BaseLLM
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

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

async def market_monitor_node(state: UnifiedState) -> Dict[str, Any]:
    """Handle market monitoring stage"""
    try:
        # Market monitoring logic here
        # ...
        
        # Move to news monitoring next
        return {"current_stage": WorkflowStage.NEWS_MONITORING}
    except Exception as e:
        state.api_errors.append(f"Market monitoring error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR_RECOVERY}

async def news_monitor_node(state: UnifiedState) -> Dict[str, Any]:
    """Handle news monitoring stage"""
    try:
        # Only update news every 5 cycles
        cycle_count = len(state.messages) # Simple way to track cycles
        if cycle_count % GRAPH_CONFIG["news_cycle"] == 0:
            monitor = NewsMonitor()
            state = await monitor.update_news_state(state)
            if state.narrative.pending_analyses:
                return {"current_stage": WorkflowStage.PATTERN_ANALYSIS}
        
        # Move to social monitoring
        return {"current_stage": WorkflowStage.SOCIAL_MONITORING}
    except Exception as e:
        state.api_errors.append(f"News monitoring error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR_RECOVERY}

async def social_monitor_node(state: UnifiedState) -> Dict[str, Any]:
    """Handle social monitoring stage"""
    try:
        # Check rate limits before proceeding
        if state.x_integration.rate_limits["remaining"] <= 1:
            if state.x_integration.rate_limits["reset_time"] > datetime.now():
                # Skip social monitoring this cycle
                return {"current_stage": WorkflowStage.PATTERN_ANALYSIS}
        
        # Social monitoring logic here
        # ...
        
        return {"current_stage": WorkflowStage.PATTERN_ANALYSIS}
    except Exception as e:
        state.api_errors.append(f"Social monitoring error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR_RECOVERY}

async def pattern_analysis_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Handle pattern analysis stage"""
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
        
        patterns = await detect_patterns(context, llm)
        
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
            return {"current_stage": WorkflowStage.NARRATIVE_GENERATION}
        
        # Start next monitoring cycle if no significant patterns
        return {"current_stage": WorkflowStage.MARKET_MONITORING}
        
    except Exception as e:
        state.api_errors.append(f"Pattern analysis error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR_RECOVERY}

async def narrative_generation_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Handle narrative generation stage"""
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
        
        # Generate Gonzo's response
        response = await generate_response(context, llm)
        
        # Update narrative state
        state.analysis.generated_narrative = response.content
        
        # Queue for X if it's a significant analysis
        if response.significance > 0.7:
            state.x_integration.queued_posts.append(response.content)
            return {"current_stage": WorkflowStage.RESPONSE_POSTING}
        
        # Start next monitoring cycle
        return {"current_stage": WorkflowStage.MARKET_MONITORING}
        
    except Exception as e:
        state.api_errors.append(f"Narrative generation error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR_RECOVERY}

async def response_posting_node(state: UnifiedState) -> Dict[str, Any]:
    """Handle response posting stage"""
    try:
        # Response posting logic here
        # ...
        
        # Start next monitoring cycle
        return {"current_stage": WorkflowStage.MARKET_MONITORING}
    except Exception as e:
        state.api_errors.append(f"Response posting error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR_RECOVERY}

async def error_recovery_node(state: UnifiedState) -> Dict[str, Any]:
    """Handle error recovery stage"""
    try:
        # Log errors
        for error in state.api_errors:
            state.add_message(f"Error encountered: {error}", source="error")
        
        # Clear errors after logging
        state.api_errors.clear()
        
        # Return to market monitoring
        return {"current_stage": WorkflowStage.MARKET_MONITORING}
    except Exception as e:
        # If error recovery fails, end the workflow
        state.add_message(f"Critical error in recovery: {str(e)}", source="critical")
        return END

def create_workflow(
    llm: Optional[BaseLLM] = None,
    config: Optional[Dict[str, Any]] = None
) -> StateGraph:
    """Create the main workflow graph using unified state management.
    
    Args:
        llm: Optional language model override
        config: Optional configuration override
        
    Returns:
        Compiled workflow graph
    """
    # Initialize graph with unified state
    workflow = StateGraph(UnifiedState)
    
    # Add monitoring nodes
    workflow.add_node("market_monitor", market_monitor_node)
    workflow.add_node("news_monitor", news_monitor_node)
    workflow.add_node("social_monitor", social_monitor_node)
    
    # Add analysis and generation nodes
    workflow.add_node("pattern_analysis", lambda x: pattern_analysis_node(x, llm))
    workflow.add_node("narrative_generation", lambda x: narrative_generation_node(x, llm))
    workflow.add_node("response_posting", response_posting_node)
    
    # Add error recovery
    workflow.add_node("error_recovery", error_recovery_node)
    
    # Add conditional edges based on WorkflowStage
    workflow.add_conditional_edges(
        "market_monitor",
        lambda x: x["current_stage"].value,
        {
            WorkflowStage.NEWS_MONITORING.value: "news_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "news_monitor",
        lambda x: x["current_stage"].value,
        {
            WorkflowStage.SOCIAL_MONITORING.value: "social_monitor",
            WorkflowStage.PATTERN_ANALYSIS.value: "pattern_analysis",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "social_monitor",
        lambda x: x["current_stage"].value,
        {
            WorkflowStage.PATTERN_ANALYSIS.value: "pattern_analysis",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "pattern_analysis",
        lambda x: x["current_stage"].value,
        {
            WorkflowStage.NARRATIVE_GENERATION.value: "narrative_generation",
            WorkflowStage.MARKET_MONITORING.value: "market_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "narrative_generation",
        lambda x: x["current_stage"].value,
        {
            WorkflowStage.RESPONSE_POSTING.value: "response_posting",
            WorkflowStage.MARKET_MONITORING.value: "market_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "response_posting",
        lambda x: x["current_stage"].value,
        {
            WorkflowStage.MARKET_MONITORING.value: "market_monitor",
            WorkflowStage.ERROR_RECOVERY.value: "error_recovery"
        }
    )
    
    workflow.add_conditional_edges(
        "error_recovery",
        lambda x: x["current_stage"].value,
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
    
    # Add system prompt to messages
    initial_state.add_message(
        SYSTEM_PROMPT,
        source="system"
    )
    
    return initial_state.model_dump()