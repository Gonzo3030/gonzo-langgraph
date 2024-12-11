from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .client import XClient
from ...types.social import Post
from ...state.x_state import MonitoringState

class ContentDiscovery(BaseModel):
    """Proactive content discovery for X platform.
    
    This component actively searches for relevant content based on configured
    topics, trends, and user interests. It serves as the primary input source
    for Gonzo's analysis pipeline.
    """
    
    class Config:
        arbitrary_types_allowed = True
    
    client: XClient = Field(default_factory=XClient)
    max_results_per_query: int = 100
    min_engagement_threshold: int = 10
    
    async def discover_content(self, state: MonitoringState) -> List[Post]:
        """Proactively discover relevant content across different sources."""
        discovered_posts = []
        
        # Get trending topics if we haven't recently
        if self._should_refresh_trends(state):
            await self._update_trending_topics(state)
        
        # Discover content from multiple sources
        trending_posts = await self._get_trending_content(state)
        topic_posts = await self._get_topic_content(state)
        user_posts = await self._get_user_content(state)
        
        discovered_posts.extend(trending_posts)
        discovered_posts.extend(topic_posts)
        discovered_posts.extend(user_posts)
        
        # Update state with discovery metrics
        self._update_discovery_metrics(state, discovered_posts)
        
        return discovered_posts
    
    async def _get_trending_content(self, state: MonitoringState) -> List[Post]:
        """Get content from current trending topics."""
        posts = []
        for trend in state.current_trends:
            try:
                trend_posts = await self.client.search_recent(
                    query=trend,
                    max_results=self.max_results_per_query
                )
                posts.extend(trend_posts)
            except Exception as e:
                state.log_error(f"Error fetching trend {trend}: {str(e)}")
        return posts
    
    async def _get_topic_content(self, state: MonitoringState) -> List[Post]:
        """Get content from tracked topics."""
        posts = []
        for topic in state.tracked_topics:
            try:
                topic_posts = await self.client.search_recent(
                    query=topic,
                    max_results=self.max_results_per_query
                )
                posts.extend(topic_posts)
            except Exception as e:
                state.log_error(f"Error fetching topic {topic}: {str(e)}")
        return posts
    
    async def _get_user_content(self, state: MonitoringState) -> List[Post]:
        """Get content from tracked users."""
        posts = []
        for user_id in state.tracked_users:
            try:
                user_posts = await self.client.get_user_posts(user_id)
                posts.extend(user_posts)
            except Exception as e:
                state.log_error(f"Error fetching user {user_id}: {str(e)}")
        return posts
    
    async def _update_trending_topics(self, state: MonitoringState) -> None:
        """Update the list of trending topics."""
        try:
            trends = await self.client.get_trends()
            state.current_trends = trends
            state.last_trends_update = datetime.now()
        except Exception as e:
            state.log_error(f"Error updating trends: {str(e)}")
    
    def _should_refresh_trends(self, state: MonitoringState) -> bool:
        """Check if we should refresh trending topics."""
        if not state.last_trends_update:
            return True
        hours_since_update = (datetime.now() - state.last_trends_update).total_seconds() / 3600
        return hours_since_update >= 1  # Refresh trends hourly
    
    def _update_discovery_metrics(self, state: MonitoringState, posts: List[Post]) -> None:
        """Update content discovery metrics in state."""
        now = datetime.now()
        state.discovery_metrics.update({
            'last_discovery_time': now,
            'posts_discovered': len(posts),
            'discovery_sources': {
                'trends': len([p for p in posts if p.source == 'trend']),
                'topics': len([p for p in posts if p.source == 'topic']),
                'users': len([p for p in posts if p.source == 'user'])
            }
        })