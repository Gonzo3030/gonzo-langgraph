from typing import Dict, Any, TypeVar, Optional
from langchain_core.runnables import RunnableConfig
from langsmith import traceable
from ...integrations.x.client import XClient
from ...integrations.x.monitor import ContentMonitor
from ...integrations.x.queue_manager import QueueManager
from ...types.base import GonzoState
from .base import update_state, log_step

StateType = TypeVar("StateType")

class XNodes:
    """Graph nodes for X integration in the LangGraph workflow."""
    
    def __init__(self):
        self.client = XClient()
        self.monitor = ContentMonitor()
        self.queue_manager = QueueManager()
    
    @traceable(name="monitor_content")
    async def monitor_content(self, state: GonzoState, config: Optional[RunnableConfig] = None) -> Dict[str, GonzoState]:
        """Node for monitoring X content and mentions."""
        try:
            # Initialize X state if needed
            if not state.x_state:
                state.initialize_x_state()
            
            # Monitor mentions
            await self.monitor.process_mentions(state.x_state)
            
            # Update metrics for recent posts
            await self.monitor.update_metrics(state.x_state)
            
            # Check tracked topics
            if state.monitoring_state:
                new_posts = await self.monitor.check_topics(state.monitoring_state)
                if new_posts:
                    state.new_content.extend(new_posts)
            
            log_step(state, "monitor_content", {
                "new_posts": len(state.new_content),
                "mentions_processed": len(state.x_state.interaction_queue.pending)
            })
            
        except Exception as e:
            state.add_error(f"Error in content monitoring: {str(e)}")
        
        return {"state": state}
    
    @traceable(name="process_queues")
    async def process_queues(self, state: GonzoState, config: Optional[RunnableConfig] = None) -> Dict[str, GonzoState]:
        """Node for processing post and interaction queues."""
        try:
            if not state.x_state:
                state.initialize_x_state()
            
            # Process post queue
            posted = await self.queue_manager.process_post_queue(state.x_state)
            if posted:
                state.posted_content.append(posted)
            
            # Process interaction queue
            reply = await self.queue_manager.process_interaction_queue(state.x_state)
            if reply:
                state.interactions.append(reply)
            
            log_step(state, "process_queues", {
                "posts_processed": len(state.posted_content),
                "interactions_processed": len(state.interactions)
            })
                
        except Exception as e:
            state.add_error(f"Error processing queues: {str(e)}")
        
        return {"state": state}
    
    @traceable(name="queue_post")
    async def queue_post(self, state: GonzoState, content: str, 
                      priority: int = 1, config: Optional[RunnableConfig] = None) -> Dict[str, GonzoState]:
        """Node for adding content to the post queue."""
        try:
            if not state.x_state:
                state.initialize_x_state()
                
            self.queue_manager.add_post(
                state=state.x_state,
                content=content,
                priority=priority
            )
            
            log_step(state, "queue_post", {
                "content": content,
                "priority": priority
            })
            
        except Exception as e:
            state.add_error(f"Error queueing post: {str(e)}")
        
        return {"state": state}
    
    @traceable(name="queue_reply")
    async def queue_reply(self, state: GonzoState, content: str, 
                       reply_to_id: str, priority: int = 1,
                       config: Optional[RunnableConfig] = None) -> Dict[str, GonzoState]:
        """Node for adding replies to the interaction queue."""
        try:
            if not state.x_state:
                state.initialize_x_state()
                
            self.queue_manager.add_reply(
                state=state.x_state,
                content=content,
                reply_to_id=reply_to_id,
                priority=priority
            )
            
            log_step(state, "queue_reply", {
                "content": content,
                "reply_to": reply_to_id,
                "priority": priority
            })
            
        except Exception as e:
            state.add_error(f"Error queueing reply: {str(e)}")
        
        return {"state": state}