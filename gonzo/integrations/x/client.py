from typing import Dict, List, Optional
from datetime import datetime
from ...config import get_api_keys
from ...types.social import Post, PostMetrics

class XClient:
    """Client for interacting with X API."""
    
    def __init__(self):
        keys = get_api_keys()
        self.client_key = keys['x_api_key']
        self.client_secret = keys['x_api_secret']
        self.access_token = keys['x_access_token']
        self.access_secret = keys['x_access_secret']
    
    async def search_recent(self, query: str, max_results: int = 100) -> List[Post]:
        """Search for recent posts matching query.
        For testing, returns mock data.
        """
        # Mock implementation
        return [
            Post(
                id="test_id",
                platform="x",
                content=f"Test post about {query}",
                created_at=datetime.now(),
                metrics=PostMetrics(likes=100, replies=10)
            )
        ]
    
    async def get_user_posts(self, user_id: str) -> List[Post]:
        """Get posts from a specific user.
        For testing, returns mock data.
        """
        return [
            Post(
                id="user_post_id",
                platform="x",
                content=f"Post from user {user_id}",
                created_at=datetime.now(),
                metrics=PostMetrics(likes=75, replies=8)
            )
        ]
    
    async def fetch_metrics(self, post_id: str) -> PostMetrics:
        """Fetch metrics for a specific post.
        For testing, returns mock data.
        """
        return PostMetrics(
            likes=100,
            replies=10,
            reposts=5,
            views=1000
        )