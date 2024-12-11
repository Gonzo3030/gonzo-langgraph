from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ...state.x_state import XState, MonitoringState
from ...types.social import Post, QueuedPost
from .client import XClient
from .content_filter import ContentFilter

class ContentMonitor:
    """Enhanced content monitor for X with filtering and state management."""
    
    def __init__(self, check_interval: int = 300):
        self.client = XClient()
        self.content_filter = ContentFilter()
        self.check_interval = check_interval  # Time between checks in seconds
    
    async def check_topics(self, state: MonitoringState) -> List[Post]:
        """Check tracked topics for new content with improved filtering.
        
        Args:
            state: Current monitoring state
            
        Returns:
            List of relevant filtered posts
        """
        posts = []
        current_time = datetime.now()
        
        for topic in state.tracked_topics:
            last_check = state.last_check_times.get(f'topic:{topic}')
            should_check = not last_check or \
                         (current_time - last_check).seconds >= self.check_interval
            
            if should_check:
                try:
                    # Get new posts for topic
                    new_posts = await self.client.search_recent(topic)
                    
                    # Apply content filtering
                    filtered_posts = self.content_filter.filter_content(
                        new_posts,
                        context={'topic': topic}
                    )
                    
                    posts.extend(filtered_posts)
                    state.last_check_times[f'topic:{topic}'] = current_time
                    
                except Exception as e:
                    state.log_error(f"Error checking topic {topic}: {str(e)}")
        
        return posts
    
    async def process_mentions(self, state: XState) -> None:
        """Process new mentions with improved handling."""
        try:
            mentions = await self.client.fetch_mentions(state)
            filtered_mentions = self.content_filter.filter_content(
                mentions,
                context={'is_mention': True}
            )
            
            for mention in filtered_mentions:
                queued = QueuedPost(
                    content="",  # To be filled by response generator
                    reply_to_id=mention.id,
                    priority=self._calculate_priority(mention),
                    context={'mention': mention.dict()}
                )
                state.interaction_queue.add_interaction(queued)
                
        except Exception as e:
            state.log_error(f"Error processing mentions: {str(e)}")
    
    async def update_metrics(self, state: XState) -> None:
        """Update metrics for recent posts with error handling."""
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
        """Calculate interaction priority based on post metrics."""
        if not post.metrics:
            return 1
        
        # Basic priority calculation
        priority = 1
        
        # Increase priority based on engagement
        if post.metrics.likes > 100 or post.metrics.replies > 20:
            priority += 1
        if post.metrics.reposts > 50:
            priority += 1
            
        return priority
