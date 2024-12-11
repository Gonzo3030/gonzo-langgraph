import tweepy
from typing import Dict, List, Optional
from datetime import datetime
from ...config import get_api_keys

class XClient:
    def __init__(self):
        keys = get_api_keys()
        self.client = tweepy.Client(
            consumer_key=keys['x_api_key'],
            consumer_secret=keys['x_api_secret'],
            access_token=keys['x_access_token'],
            access_token_secret=keys['x_access_token_secret']
        )
        self.last_post_time = None
        self.daily_counts = {
            'posts': 0,
            'replies': 0
        }
    
    async def post_update(self, content: str) -> Dict:
        """Post an update with rate limiting."""
        if not self._can_post():
            raise Exception("Post limit reached or too soon since last post")
        
        response = self.client.create_tweet(text=content)
        self._update_counts('posts')
        self.last_post_time = datetime.now()
        return response.data
    
    async def reply_to_post(self, post_id: str, content: str) -> Dict:
        """Reply to a specific post."""
        if not self._can_reply():
            raise Exception("Reply limit reached")
        
        response = self.client.create_tweet(
            text=content,
            in_reply_to_tweet_id=post_id
        )
        self._update_counts('replies')
        return response.data
    
    def _can_post(self) -> bool:
        """Check if we can post based on limits."""
        if self.daily_counts['posts'] >= 100:  # Daily limit
            return False
        
        if self.last_post_time:
            time_since_last = (datetime.now() - self.last_post_time).seconds
            if time_since_last < 60:  # At least 1 minute between posts
                return False
        
        return True
    
    def _can_reply(self) -> bool:
        """Check if we can reply based on limits."""
        return self.daily_counts['replies'] < 100  # Daily limit
    
    def _update_counts(self, action_type: str) -> None:
        """Update daily action counts."""
        self.daily_counts[action_type] += 1