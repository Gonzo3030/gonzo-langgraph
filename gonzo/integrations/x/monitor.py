from typing import List
from datetime import datetime
from ...state.x_state import XState, MonitoringState
from ...types.social import Post, QueuedPost
from .client import XClient

class ContentMonitor:
    """Monitors X for content and interactions."""
    
    def __init__(self):
        self.client = XClient()
    
    async def check_topics(self, state: MonitoringState) -> List[Post]:
        """Check tracked topics for new content."""
        posts = []
        for topic in state.tracked_topics:
            last_check = state.last_check_times.get(f'topic:{topic}')
            if not last_check or (datetime.now() - last_check).seconds > 300:
                # Here we'd query for new content
                # Mock response for testing
                test_post = Post(
                    id='123',
                    platform='x',
                    content=f'Test post about {topic}',
                    created_at=datetime.now()
                )
                posts.append(test_post)
                state.last_check_times[f'topic:{topic}'] = datetime.now()
        return posts
    
    async def process_mentions(self, state: XState) -> None:
        """Process new mentions."""
        mentions = await self.client.fetch_mentions(state)
        for mention in mentions:
            queued = QueuedPost(
                content="",  # To be filled by response generator
                reply_to_id=mention.id,
                priority=1
            )
            state.interaction_queue.add_interaction(queued)
    
    async def update_metrics(self, state: XState) -> None:
        """Update metrics for recent posts."""
        recent_posts = state.post_history.get_recent_posts()
        for post in recent_posts:
            metrics = await self.client.fetch_metrics(state, post.id)
            post.metrics = metrics