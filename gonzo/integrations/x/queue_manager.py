from typing import Optional
from datetime import datetime
from ...state.x_state import XState
from ...types.social import QueuedPost, Post
from .client import XClient

class QueueManager:
    """Manages post and interaction queues for X."""
    
    def __init__(self):
        self.client = XClient()
    
    async def process_post_queue(self, state: XState) -> Optional[Post]:
        """Process the next item in the post queue."""
        if not state.post_queue:
            return None
            
        # Get highest priority post
        post = sorted(state.post_queue, key=lambda x: x.priority, reverse=True)[0]
        
        # Remove from queue
        state.post_queue.remove(post)
        
        # Post to X
        posted = await self.client.post_update(state, post)
        return posted
    
    async def process_interaction_queue(self, state: XState) -> Optional[Post]:
        """Process the next interaction in the queue."""
        next_interaction = state.interaction_queue.get_next()
        if not next_interaction:
            return None
            
        # Remove from pending
        state.interaction_queue.pending.remove(next_interaction)
        
        # Add to processing
        state.interaction_queue.processing.append(next_interaction.reply_to_id)
        
        try:
            # Post reply
            posted = await self.client.post_update(state, next_interaction)
            
            # Remove from processing
            state.interaction_queue.processing.remove(next_interaction.reply_to_id)
            
            return posted
            
        except Exception as e:
            if next_interaction.reply_to_id in state.interaction_queue.processing:
                state.interaction_queue.processing.remove(next_interaction.reply_to_id)
            raise
    
    def add_post(self, state: XState, content: str, priority: int = 1) -> None:
        """Add a new post to the queue."""
        post = QueuedPost(
            content=content,
            priority=priority
        )
        state.add_to_post_queue(post)
        
    def add_reply(self, state: XState, content: str, reply_to_id: str,
                 priority: int = 1, context: dict = {}) -> None:
        """Add a new reply to the interaction queue."""
        post = QueuedPost(
            content=content,
            priority=priority,
            reply_to_id=reply_to_id,
            context=context
        )
        state.interaction_queue.add_interaction(post)