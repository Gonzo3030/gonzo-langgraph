"""Core workflow implementation for Gonzo using LangGraph"""
import os
from typing import Dict, Any, Callable
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain.chat_models import ChatOpenAI
import asyncio

from .state_management import (
    UnifiedState,
    WorkflowStage,
    create_initial_state,
    update_state
)

from .nodes.monitoring import process_market_data, monitor_social_feeds
from .nodes.rag import perform_rag_analysis
from .nodes.patterns import detect_patterns
from .nodes.assessment import assess_content
from .nodes.narrative import generate_narrative
from .nodes.evolution import evolve_agent
from .nodes.x_integration import post_content, handle_interactions

# Node Implementation

async def monitor_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Content monitoring and initial processing"""
    try:
        # Process market data
        market_data = await process_market_data()
        state.knowledge_graph.entities.update(market_data)
        
        # Monitor social feeds
        social_data = await monitor_social_feeds()
        state.current_context.update(social_data)
        
        return {
            "current_stage": WorkflowStage.RAG_ANALYSIS,
            "checkpoint_needed": True
        }
    except Exception as e:
        state.record_error(f"Monitor error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def rag_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """RAG analysis and context building"""
    try:
        rag_results = await perform_rag_analysis(
            state.current_context,
            state.knowledge_graph,
            llm
        )
        
        state.memory.semantic.update(rag_results.context)
        state.assessment.content_analysis.update(rag_results.analysis)
        
        return {"current_stage": WorkflowStage.PATTERN_DETECT}
    except Exception as e:
        state.record_error(f"RAG error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def pattern_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Pattern detection and analysis"""
    try:
        patterns = await detect_patterns(
            state.assessment.content_analysis,
            state.knowledge_graph.patterns,
            llm
        )
        
        state.knowledge_graph.patterns.extend(patterns)
        
        return {
            "current_stage": WorkflowStage.ASSESS,
            "checkpoint_needed": True
        }
    except Exception as e:
        state.record_error(f"Pattern detection error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def assessment_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Content assessment and analysis"""
    try:
        assessment_results = await assess_content(
            state.knowledge_graph,
            state.assessment,
            llm
        )
        
        state.assessment = assessment_results
        state.narrative.context.update({
            "assessment": assessment_results,
            "patterns": state.knowledge_graph.patterns
        })
        
        return {"current_stage": WorkflowStage.NARRATE}
    except Exception as e:
        state.record_error(f"Assessment error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def narrative_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Narrative generation"""
    try:
        narrative = await generate_narrative(
            state.narrative.context,
            state.memory,
            llm
        )
        
        state.narrative.story_elements = narrative.elements
        state.x_integration.queued_posts = narrative.posts
        
        return {
            "current_stage": WorkflowStage.QUEUE,
            "checkpoint_needed": True
        }
    except Exception as e:
        state.record_error(f"Narrative generation error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def queue_node(state: UnifiedState) -> Dict[str, Any]:
    """Post queue management"""
    try:
        if not state.x_integration.queued_posts:
            return {"current_stage": WorkflowStage.MONITOR}
            
        # Check rate limits
        if state.x_integration.rate_limits.get("post_limit"):
            if datetime.utcnow() < state.x_integration.rate_limits["post_limit"]:
                return {"current_stage": WorkflowStage.QUEUE}
        
        return {"current_stage": WorkflowStage.POST}
    except Exception as e:
        state.record_error(f"Queue error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def post_node(state: UnifiedState) -> Dict[str, Any]:
    """Content posting to X"""
    try:
        post_result = await post_content(state.x_integration)
        
        if post_result.success:
            state.x_integration.post_history.append(post_result.post_data)
            state.x_integration.queued_posts.pop(0)
            
            return {
                "current_stage": WorkflowStage.INTERACT,
                "checkpoint_needed": True
            }
        else:
            state.record_error(f"Posting error: {post_result.error}")
            return {"current_stage": WorkflowStage.ERROR}
    except Exception as e:
        state.record_error(f"Post error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def interaction_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Handle X interactions"""
    try:
        interactions = await handle_interactions(
            state.x_integration,
            state.memory,
            llm
        )
        
        state.x_integration.interactions.extend(interactions)
        
        return {
            "current_stage": WorkflowStage.EVOLVE,
            "checkpoint_needed": True
        }
    except Exception as e:
        state.record_error(f"Interaction error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

async def evolution_node(state: UnifiedState, llm: Any) -> Dict[str, Any]:
    """Agent evolution and learning"""
    try:
        evolution_result = await evolve_agent(
            state.evolution,
            state.memory,
            state.x_integration.interactions,
            llm
        )
        
        state.evolution = evolution_result
        state.memory.procedural.update(evolution_result.learned_behaviors)
        
        return {"current_stage": WorkflowStage.MONITOR}
    except Exception as e:
        state.record_error(f"Evolution error: {str(e)}")
        return {"current_stage": WorkflowStage.ERROR}

# Workflow Creation

def create_node_fn(func: Callable, llm: Any = None) -> Callable:
    """Create a node function with proper state handling"""
    async def wrapper(state_dict: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Convert dict to UnifiedState
            state = UnifiedState(**state_dict)
            
            # Execute node logic
            if llm:
                result = await func(state, llm)
            else:
                result = await func(state)
                
            # Handle checkpointing
            if state.checkpoint_needed:
                # Implement checkpoint saving logic here
                pass
                
            return result
        except Exception as e:
            return {
                "current_stage": WorkflowStage.ERROR,
                "last_error": str(e)
            }
    
    def sync_wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(wrapper(state))
    
    return sync_wrapper

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow"""
    # Initialize workflow with UnifiedState
    workflow = StateGraph(UnifiedState)
    
    # Initialize LLMs
    primary_llm = ChatAnthropic(
        model="claude-3-opus-20240229",
        temperature=0.7,
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )
    
    backup_llm = ChatOpenAI(
        temperature=0.7,
        model="gpt-4-turbo-preview"
    )
    
    # Add all nodes
    workflow.add_node("monitor", create_node_fn(monitor_node, primary_llm))
    workflow.add_node("rag", create_node_fn(rag_node, primary_llm))
    workflow.add_node("pattern", create_node_fn(pattern_node, primary_llm))
    workflow.add_node("assess", create_node_fn(assessment_node, primary_llm))
    workflow.add_node("narrate", create_node_fn(narrative_node, primary_llm))
    workflow.add_node("queue", create_node_fn(queue_node))
    workflow.add_node("post", create_node_fn(post_node))
    workflow.add_node("interact", create_node_fn(interaction_node, backup_llm))
    workflow.add_node("evolve", create_node_fn(evolution_node, primary_llm))
    
    # Add conditional edges
    for stage in WorkflowStage:
        if stage != WorkflowStage.END:
            workflow.add_conditional_edges(
                stage.value,
                lambda state: state["current_stage"]
            )
    
    # Add error handling
    workflow.add_edge("error", END)
    
    # Set entry point
    workflow.set_entry_point("monitor")
    
    return workflow.compile()

def initialize_workflow() -> Dict[str, Any]:
    """Initialize the workflow with a clean state"""
    return create_initial_state().model_dump()
