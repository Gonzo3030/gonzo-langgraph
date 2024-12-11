from typing import Dict, Any, Optional
from datetime import datetime
import tweepy
from ...state.x_state import XState
from ...types.social import Post, PostMetrics, QueuedPost
from ...config import get_api_keys

class XClient:
    """X (Twitter) API client with rate limiting."""
    
    def __init__(self):
        keys = get_api_keys()
        self.client = tweepy.Client(
            bearer_token=keys['x_bearer_token'],
            consumer_key=keys['x_api_key'],
            consumer_secret=keys['x_api_secret'],
            access_token=keys['x_access_token'],
            access_token_secret=keys['x_access_token_secret']
        )
    
    async def post_update(self, state: XState, post: QueuedPost) -> Post:
        """Post an update to X."""
        response = self.client.create_tweet(
            text=post.content,
            in_reply_to_tweet_id=post.reply_to_id
        )
        
        posted = Post(
            id=str(response.data['id']),
            platform='x',
            content=post.content,
            created_at=datetime.now(),
            reply_to_id=post.reply_to_id
        )
        
        # Update state
        state.record_post(posted)
        return posted
    
    async def fetch_metrics(self, state: XState, post_id: str) -> PostMetrics:
        """Fetch metrics for a post."""
        tweet = self.client.get_tweet(
            id=post_id,
            tweet_fields=['public_metrics']
        )
        
        metrics = tweet.data.public_metrics
        return PostMetrics(
            likes=metrics['like_count'],
            replies=metrics['reply_count'],
            reposts=metrics['retweet_count'],
            views=metrics.get('impression_count', 0)
        )