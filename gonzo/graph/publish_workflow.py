"""Publishing workflow implementation for Gonzo."""
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..state_management import WorkflowStage, GonzoGraphState
from ..publishing.publisher import Publisher

logger = logging.getLogger(__name__)

def get_datetime(value: Any) -> Optional[datetime]:
    """Convert various datetime formats to datetime object."""
    if isinstance(value, datetime):
        return value
    elif isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    elif isinstance(value, dict) and 'isoformat' in value:
        try:
            return datetime.fromisoformat(value['isoformat'])
        except ValueError:
            return None
    return None

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
        
        # Clean up old posts and sort by scheduled time
        current_time = datetime.now()
        ready_posts = []
        remaining_posts = []
        
        for post in queued_posts:
            try:
                scheduled_time = get_datetime(post.get('scheduled_time'))
                if not scheduled_time:
                    logger.warning(f"Could not parse scheduled time from post: {post.get('scheduled_time')}")
                    continue
                
                # Skip posts older than 24 hours
                if current_time - scheduled_time > timedelta(hours=24):
                    logger.info(f"Skipping post scheduled for {scheduled_time} (too old)")
                    continue
                    
                if scheduled_time <= current_time:
                    logger.info(f"Found post ready for publishing (scheduled: {scheduled_time})")
                    ready_posts.append(post)
                else:
                    logger.info(f"Post scheduled for later: {scheduled_time}")
                    remaining_posts.append(post)
                    
            except Exception as e:
                logger.warning(f"Error processing post: {str(e)}")
        
        if not ready_posts:
            logger.info("No posts ready for publishing")
            if len(remaining_posts) != len(queued_posts):
                logger.info(f"Cleaned {len(queued_posts) - len(remaining_posts)} old posts from queue")
            return {
                "queued_posts": remaining_posts,
                "current_stage": WorkflowStage.COMPLETE.value
            }
            
        logger.info(f"Found {len(ready_posts)} posts ready for publishing, {len(remaining_posts)} remaining in queue")
        return {
            "ready_posts": ready_posts[:1],  # Only take one post at a time
            "remaining_posts": remaining_posts + ready_posts[1:],  # Keep others in queue
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
        published_posts = state.get('published_posts', [])
        
        if not ready_posts:
            return {
                "current_stage": WorkflowStage.COMPLETE.value
            }
        
        # Initialize publisher
        publisher = Publisher.from_env(wait_time=10.0)  # Increased base wait time
        
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
                            'result': result,
                            'published_at': datetime.now()
                        })
                        logger.info("Successfully published thread")
                    else:
                        # Only retry rate limit errors
                        error = str(result.get('error', '')).lower()
                        if 'too many requests' in error or '429' in error:
                            failed.append(post)
                            logger.info("Rate limited, will retry later")
                        else:
                            logger.warning(f"Dropping post due to non-retryable error: {error}")
            except Exception as e:
                logger.error(f"Error publishing post: {str(e)}")
        
        # Update state
        return {
            "published_posts": published_posts + published,
            "queued_posts": remaining_posts + failed,
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

def create_publish_workflow(config: Optional[Dict[str, Any]] = None) -> tuple[StateGraph, MemorySaver]:
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