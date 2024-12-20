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

# Core state management
def ensure_unified_state(state: Union[Dict, UnifiedState]) -> UnifiedState:
    """Ensure we're working with a UnifiedState object."""
    if isinstance(state, dict):
        return UnifiedState(**state)
    return state

[... monitoring nodes remain the same ...]

# Analysis nodes
def pattern_analysis_node(state: Union[Dict, UnifiedState], llm: BaseLLM) -> Dict[str, Any]:
    """Handle pattern analysis stage."""
    state = ensure_unified_state(state)
    
    try:
        if state.narrative.pending_analyses:
            # Prepare context for pattern detection
            context = {
                'market_events': state.narrative.market_events,
                'news_events': state.narrative.news_events,
                'social_events': state.narrative.social_events,
                'previous_patterns': state.narrative.patterns
            }
            
            # Detect patterns using LLM
            patterns = detect_patterns(context, llm)
            state.narrative.patterns.extend(patterns)
            
            # If significant patterns found, move to narrative generation
            if any(p.significance > GRAPH_CONFIG['pattern_significance_threshold'] 
                   for p in patterns):
                state.current_stage = WorkflowStage.NARRATIVE_GENERATION
            else:
                state.current_stage = WorkflowStage.CYCLE_COMPLETE
        else:
            state.current_stage = WorkflowStage.CYCLE_COMPLETE
        
    except Exception as e:
        state.api_errors.append(f"Pattern analysis error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def narrative_generation_node(state: Union[Dict, UnifiedState], llm: BaseLLM) -> Dict[str, Any]:
    """Handle narrative generation stage."""
    state = ensure_unified_state(state)
    
    try:
        # Generate narrative using LLM
        narrative = generate_response(
            patterns=state.narrative.patterns,
            market_events=state.narrative.market_events,
            news_events=state.narrative.news_events,
            social_events=state.narrative.social_events,
            llm=llm
        )
        
        if narrative and narrative.content:
            state.analysis.generated_narrative = narrative.content
            state.analysis.significance = narrative.significance
            
            if narrative.significance > GRAPH_CONFIG['posting_threshold']:
                state.current_stage = WorkflowStage.RESPONSE_POSTING
            else:
                state.current_stage = WorkflowStage.CYCLE_COMPLETE
        else:
            state.current_stage = WorkflowStage.CYCLE_COMPLETE
        
    except Exception as e:
        state.api_errors.append(f"Narrative generation error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()

def response_posting_node(state: Union[Dict, UnifiedState]) -> Dict[str, Any]:
    """Handle response posting stage."""
    state = ensure_unified_state(state)
    
    try:
        if state.analysis.generated_narrative:
            # TODO: Implement actual posting logic
            state.messages.append(f"Would post: {state.analysis.generated_narrative}")
        
        state.current_stage = WorkflowStage.CYCLE_COMPLETE
        
    except Exception as e:
        state.api_errors.append(f"Response posting error: {str(e)}")
        state.current_stage = WorkflowStage.ERROR_RECOVERY
    
    return state.model_dump()