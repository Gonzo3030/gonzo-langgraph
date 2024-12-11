from typing import Dict, Any, Tuple
from langchain.pydantic_v1 import BaseModel
from ...integrations.x.client import XClient
from ...integrations.x.monitor import ContentMonitor
from ...integrations.x.queue_manager import QueueManager
from ...state.x_state import XState

class XNodes:
    """Graph nodes for X integration in the LangGraph workflow."""
    
    def __init__(self):
        self.client = XClient()
        self.monitor = ContentMonitor()
        self.queue_manager = QueueManager()
    
    async def monitor_content(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for monitoring X content and mentions."""
        x_state = state.get('x_state', XState())
        
        try:
            # Monitor mentions
            await self.monitor.process_mentions(x_state)
            
            # Update metrics for recent posts
            await self.monitor.update_metrics(x_state)
            
            # Check tracked topics
            if hasattr(state, 'monitoring_state'):
                new_posts = await self.monitor.check_topics(state.monitoring_state)
                if new_posts:
                    if 'new_content' not in state:
                        state['new_content'] = []
                    state['new_content'].extend(new_posts)
            
        except Exception as e:
            x_state.log_error(f"Error in content monitoring: {str(e)}")
        
        state['x_state'] = x_state
        return state
    
    async def process_queues(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for processing post and interaction queues."""
        x_state = state.get('x_state', XState())
        
        try:
            # Process post queue
            posted = await self.queue_manager.process_post_queue(x_state)
            if posted:
                if 'posted_content' not in state:
                    state['posted_content'] = []
                state['posted_content'].append(posted)
            
            # Process interaction queue
            reply = await self.queue_manager.process_interaction_queue(x_state)
            if reply:
                if 'interactions' not in state:
                    state['interactions'] = []
                state['interactions'].append(reply)
                
        except Exception as e:
            x_state.log_error(f"Error processing queues: {str(e)}")
        
        state['x_state'] = x_state
        return state
    
    async def queue_post(self, state: Dict[str, Any], content: str, 
                      priority: int = 1) -> Dict[str, Any]:
        """Node for adding content to the post queue."""
        x_state = state.get('x_state', XState())
        
        try:
            self.queue_manager.add_post(
                state=x_state,
                content=content,
                priority=priority
            )
        except Exception as e:
            x_state.log_error(f"Error queueing post: {str(e)}")
        
        state['x_state'] = x_state
        return state
    
    async def queue_reply(self, state: Dict[str, Any], content: str, 
                       reply_to_id: str, priority: int = 1) -> Dict[str, Any]:
        """Node for adding replies to the interaction queue."""
        x_state = state.get('x_state', XState())
        
        try:
            self.queue_manager.add_reply(
                state=x_state,
                content=content,
                reply_to_id=reply_to_id,
                priority=priority
            )
        except Exception as e:
            x_state.log_error(f"Error queueing reply: {str(e)}")
        
        state['x_state'] = x_state
        return state