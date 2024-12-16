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
    create_initial_state,
    update_state
)
from ..nodes.initial_assessment import initial_assessment
from ..nodes.pattern_detection import detect_patterns
from ..nodes.response_generation import generate_response

# Node Wrappers

async def assessment_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Wrapper for assessment logic with new state management"""
    try:
        # Convert current context for assessment
        assessment_result = await initial_assessment(
            state.current_context,
            llm
        )
        
        # Update state with assessment results
        state.assessment.content_analysis.update(assessment_result.analysis)
        state.assessment.entity_extraction.extend(assessment_result.entities)
        state.assessment.sentiment_analysis.update(assessment_result.sentiment)
        
        return {
            "current_stage": WorkflowStage.PATTERN_DETECT,
            "checkpoint_needed": True
        }
    except Exception as e:
        state.record_error(f"Assessment error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def pattern_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Wrapper for pattern detection with new state management"""
    try:
        patterns = await detect_patterns(
            state.assessment.content_analysis,
            state.knowledge_graph.patterns,
            llm
        )
        
        # Update state with detected patterns
        state.knowledge_graph.patterns.extend(patterns)
        
        # Only proceed to narrative if significant patterns found
        if patterns and any(p.get('significance', 0) > 0.5 for p in patterns):
            return {"current_stage": WorkflowStage.NARRATE}
        else:
            return {"current_stage": WorkflowStage.MONITOR}
            
    except Exception as e:
        state.record_error(f"Pattern detection error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def narrative_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Wrapper for narrative generation with new state management"""
    try:
        # Build context for narrative generation
        context = {
            "messages": state.messages,
            "patterns": state.knowledge_graph.patterns,
            "assessment": state.assessment.content_analysis
        }
        
        # Generate Gonzo's response
        response = await generate_response(context, llm)
        
        # Update narrative state
        state.narrative.story_elements.append({
            "timestamp": datetime.utcnow(),
            "content": response.content,
            "type": response.response_type
        })
        
        # Queue for X if it's a significant analysis
        if response.significance > 0.7:
            state.x_integration.queued_posts.append(response.content)
            return {"current_stage": WorkflowStage.QUEUE}
        
        return {"current_stage": WorkflowStage.MONITOR}
        
    except Exception as e:
        state.record_error(f"Narrative generation error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

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
    
    # Add nodes
    workflow.add_node("assess", lambda x: assessment_node(x, llm))
    workflow.add_node("detect", lambda x: pattern_node(x, llm))
    workflow.add_node("narrate", lambda x: narrative_node(x, llm))
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "assess",
        lambda x: x["current_stage"].value
    )
    
    workflow.add_conditional_edges(
        "detect",
        lambda x: x["current_stage"].value
    )
    
    workflow.add_conditional_edges(
        "narrate",
        lambda x: x["current_stage"].value
    )
    
    # Add error handling
    workflow.add_edge("error", END)
    
    # Set entry point
    workflow.set_entry_point("assess")
    
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