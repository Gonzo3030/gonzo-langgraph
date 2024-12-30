"""Publishing workflow implementation for Gonzo."""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..state_management import WorkflowStage, GonzoGraphState
from ..publishing.publisher import Publisher

logger = logging.getLogger(__name__)

async def check_queue_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Check queue for pending posts."""
    logger.info("Checking publishing queue")
    
    try:
        queued_posts = state.get('queued_posts', [])
        if not queued_posts:
            logger.info("No posts in queue")
            return {
                "current_stage": WorkflowStage.COMPLETE.value
            }
            
        # Get the next post(s) that are ready
        ready_posts = []
        remaining_posts = []
        current_time = datetime.now()
        
        for post in queued_posts:
            scheduled_time = datetime.fromisoformat(post['scheduled_time'])
            if scheduled_time <= current_time:
                ready_posts.append(post)
            else:
                remaining_posts.append(post)
        
        if not ready_posts:
            logger.info("No posts ready for publishing")
            return {
                "current_stage": WorkflowStage.COMPLETE.value
            }
            
        return {
            "ready_posts": ready_posts,
            "remaining_posts": remaining_posts,
            "current_stage": WorkflowStage.PUBLISHING.value
        }
        
    except Exception as e:
        error_msg = f"Error checking queue: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

async def publish_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Publish ready posts."""
    logger.info("Starting publishing phase")
    
    try:
        ready_posts = state.get('ready_posts', [])
        remaining_posts = state.get('remaining_posts', [])
        
        if not ready_posts:
            return {
                "current_stage": WorkflowStage.COMPLETE.value
            }
        
        # Initialize publisher
        publisher = Publisher.from_env(wait_time=2.0)  # Increased wait time for rate limits
        
        # Publish posts
        published = []
        failed = []
        
        for post in ready_posts:
            try:
                thread = post['insight'].get('thread', [])
                if thread:
                    result = await publisher.publish_thread(thread)
                    if result.get('success'):
                        published.append({
                            'post': post,
                            'result': result
                        })
                    else:
                        failed.append({
                            'post': post,
                            'error': result.get('error')
                        })
            except Exception as e:
                failed.append({
                    'post': post,
                    'error': str(e)
                })
        
        # Update queue
        updated_queue = remaining_posts + [f['post'] for f in failed]
        
        return {
            "published_posts": published,
            "queued_posts": updated_queue,
            "current_stage": WorkflowStage.COMPLETE.value
        }
        
    except Exception as e:
        error_msg = f"Publishing error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

async def error_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Handle errors and recovery."""
    if state.get('errors'):
        for error in state['errors']:
            logger.error(f"Error encountered: {error}")
    
    return {
        "errors": [],
        "current_stage": WorkflowStage.COMPLETE.value
    }

def get_stage(state: GonzoGraphState) -> str:
    """Get stage value from state."""
    return state.get('current_stage', WorkflowStage.MONITORING.value)

def create_publish_workflow(config: Optional[Dict[str, Any]] = None) -> Tuple[StateGraph, MemorySaver]:
    """Create the publishing workflow graph."""
    # Create workflow with state schema
    workflow = StateGraph(state_schema=GonzoGraphState)
    
    # Add nodes
    workflow.add_node("check_queue", check_queue_node)
    workflow.add_node("publish", publish_node)
    workflow.add_node("error", error_node)
    
    # Add edges
    workflow.add_conditional_edges(
        "check_queue",
        get_stage,
        {
            WorkflowStage.PUBLISHING.value: "publish",
            WorkflowStage.ERROR.value: "error",
            WorkflowStage.COMPLETE.value: END
        }
    )
    
    workflow.add_conditional_edges(
        "publish",
        get_stage,
        {
            WorkflowStage.ERROR.value: "error",
            WorkflowStage.COMPLETE.value: END
        }
    )
    
    workflow.add_conditional_edges(
        "error",
        get_stage,
        {
            WorkflowStage.COMPLETE.value: END
        }
    )
    
    # Set entry point
    workflow.add_edge(START, "check_queue")
    
    # Create memory saver
    memory = MemorySaver()
    
    return workflow, memory