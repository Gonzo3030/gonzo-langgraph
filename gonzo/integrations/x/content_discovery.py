from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from .client import XClient
from ...types.social import Post
from ...state.x_state import MonitoringState
from ...config.topics import TopicConfiguration

class ContentDiscovery(BaseModel):
    """Content discovery for X platform. Finds posts related to topics of interest."""
    
    class Config:
        arbitrary_types_allowed = True
    
    client: XClient = Field(default_factory=XClient)
    max_results_per_query: int = 100
    
    async def discover_content(self, state: MonitoringState) -> List[Post]:
        """Find content related to tracked topics."""
        discovered_posts = []
        
        # Get content for each topic
        for topic in TopicConfiguration.get_all_topics():
            try:
                posts = await self.client.search_recent(
                    query=topic,
                    max_results=self.max_results_per_query
                )
                discovered_posts.extend(posts)
            except Exception as e:
                state.log_error(f"Error fetching content for {topic}: {str(e)}")
        
        # Get content from tracked users
        for user_id in state.tracked_users:
            try:
                user_posts = await self.client.get_user_posts(user_id)
                discovered_posts.extend(user_posts)
            except Exception as e:
                state.log_error(f"Error fetching user {user_id}: {str(e)}")
        
        return discovered_posts