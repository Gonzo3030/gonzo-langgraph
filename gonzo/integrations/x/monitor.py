from typing import List, Optional
from datetime import datetime
from ...state.x_state import XState, MonitoringState
from ...types.social import Post, QueuedPost
from .client import XClient
from .content_filter import ContentFilter
from .content_discovery import ContentDiscovery

class ContentMonitor:
    """Enhanced content monitor with proactive discovery and analysis capabilities."""
    
    def __init__(self):
        self.client = XClient()
        self.content_filter = ContentFilter()
        self.content_discovery = ContentDiscovery()
    
    async def monitor_cycle(self, state: XState) -> List[Post]:
        """Run a complete monitoring cycle including discovery and interaction processing.
        
        This is the main entry point that coordinates content discovery, filtering,
        and interaction processing.
        """
        all_content = []
        
        # Proactively discover new content
        discovered_content = await self.content_discovery.discover_content(state.monitoring)
        filtered_discovered = self.content_filter.filter_content(
            discovered_content,
            context={'mode': 'discovery'}
        )
        all_content.extend(filtered_discovered)
        
        # Process mentions and interactions
        mentions = await self.process_mentions(state)
        filtered_mentions = self.content_filter.filter_content(
            mentions,
            context={'mode': 'mention'}
        )
        all_content.extend(filtered_mentions)
        
        # Update metrics for existing content
        await self.update_metrics(state)
        
        # Update state
        state.last_monitor_time = datetime.now()
        
        return all_content
    
    async def process_mentions(self, state: XState) -> List[Post]:
        """Process new mentions and add to interaction queue."""
        try:
            mentions = await self.client.fetch_mentions(state)
            
            for mention in mentions:
                queued = QueuedPost(
                    content="",  # To be filled by response generator
                    reply_to_id=mention.id,
                    priority=self._calculate_priority(mention),
                    context={
                        'type': 'mention',
                        'mention_data': mention.dict()
                    }
                )
                state.interaction_queue.add_interaction(queued)
            
            return mentions
            
        except Exception as e:
            state.log_error(f"Error processing mentions: {str(e)}")
            return []
    
    async def update_metrics(self, state: XState) -> None:
        """Update metrics for tracked content."""
        recent_posts = state.post_history.get_recent_posts()
        
        for post in recent_posts:
            try:
                metrics = await self.client.fetch_metrics(state, post.id)
                post.metrics = metrics
            except Exception as e:
                state.log_error(
                    f"Error updating metrics for post {post.id}: {str(e)}",
                    context={'post_id': post.id}
                )
    
    def _calculate_priority(self, post: Post) -> int:
        """Calculate interaction priority based on post metrics and content."""
        if not post.metrics:
            return 1
        
        priority = 1
        
        # Increase priority based on engagement
        if post.metrics.likes > 100 or post.metrics.replies > 20:
            priority += 1
        if post.metrics.reposts > 50:
            priority += 1
            
        return priority