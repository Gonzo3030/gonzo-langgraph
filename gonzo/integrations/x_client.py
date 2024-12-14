"""X (Twitter) API v2 client for Gonzo."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import requests
import logging
import time
from requests_oauthlib import OAuth1Session
from pydantic import BaseModel

from ..config import (
    X_API_KEY,
    X_API_SECRET,
    X_ACCESS_TOKEN,
    X_ACCESS_SECRET
)
from ..state.x_state import XState

logger = logging.getLogger(__name__)

class Tweet(BaseModel):
    """Tweet data model."""
    id: str
    text: str
    author_id: str
    conversation_id: Optional[str] = None
    created_at: datetime
    referenced_tweets: Optional[List[Dict[str, str]]] = None
    context_annotations: Optional[List[Dict[str, Any]]] = None

class XClient:
    """Client for X API v2 interactions."""
    
    def __init__(self):
        """Initialize X client."""
        self.session = OAuth1Session(
            client_key=X_API_KEY,
            client_secret=X_API_SECRET,
            resource_owner_key=X_ACCESS_TOKEN,
            resource_owner_secret=X_ACCESS_SECRET
        )
        self.base_url = "https://api.twitter.com/2"
        self._state = XState()
    
    async def post_tweet(self, text: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """Post a tweet.
        
        Args:
            text: Tweet text
            reply_to: Optional tweet ID to reply to
            
        Returns:
            Tweet data
        """
        try:
            url = f"{self.base_url}/tweets"
            data = {"text": text}
            if reply_to:
                data["reply"] = {"in_reply_to_tweet_id": reply_to}
                
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            return response.json()["data"]
            
        except Exception as e:
            logger.error(f"Error posting tweet: {str(e)}")
            raise
    
    async def monitor_mentions(self, since_id: Optional[str] = None) -> List[Tweet]:
        """Monitor mentions of Gonzo.
        
        Args:
            since_id: Optional tweet ID to start from
            
        Returns:
            List of tweets mentioning Gonzo
        """
        try:
            # First get user ID
            me_url = f"{self.base_url}/users/me"
            me_response = self.session.get(me_url)
            me_response.raise_for_status()
            user_id = me_response.json()["data"]["id"]
            
            # Get mentions
            url = f"{self.base_url}/users/{user_id}/mentions"
            params = {
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations"
            }
            if since_id:
                params["since_id"] = since_id
                
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            
            # Convert to Tweet models
            return [
                Tweet(
                    id=tweet["id"],
                    text=tweet["text"],
                    author_id=tweet["author_id"],
                    conversation_id=tweet.get("conversation_id"),
                    created_at=datetime.fromisoformat(tweet["created_at"].replace('Z', '+00:00')),
                    referenced_tweets=tweet.get("referenced_tweets"),
                    context_annotations=tweet.get("context_annotations")
                )
                for tweet in data
            ]
                
        except Exception as e:
            logger.error(f"Error monitoring mentions: {str(e)}")
            return []
    
    async def get_conversation_thread(self, conversation_id: str) -> List[Tweet]:
        """Get conversation thread.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of tweets in conversation
        """
        try:
            url = f"{self.base_url}/tweets/search/recent"
            params = {
                "query": f"conversation_id:{conversation_id}",
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations",
                "max_results": 100
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            
            # Convert and sort tweets
            tweets = [
                Tweet(
                    id=tweet["id"],
                    text=tweet["text"],
                    author_id=tweet["author_id"],
                    conversation_id=tweet.get("conversation_id"),
                    created_at=datetime.fromisoformat(tweet["created_at"].replace('Z', '+00:00')),
                    referenced_tweets=tweet.get("referenced_tweets"),
                    context_annotations=tweet.get("context_annotations")
                )
                for tweet in data
            ]
            
            return sorted(tweets, key=lambda x: x.created_at)
                
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return []
    
    async def monitor_keywords(self, keywords: List[str], since_id: Optional[str] = None) -> List[Tweet]:
        """Monitor tweets containing keywords.
        
        Args:
            keywords: List of keywords to monitor
            since_id: Optional tweet ID to start from
            
        Returns:
            List of matching tweets
        """
        try:
            url = f"{self.base_url}/tweets/search/recent"
            query = " OR ".join(keywords)
            params = {
                "query": query,
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations",
                "max_results": 100
            }
            if since_id:
                params["since_id"] = since_id
                
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            
            # Convert to Tweet models
            return [
                Tweet(
                    id=tweet["id"],
                    text=tweet["text"],
                    author_id=tweet["author_id"],
                    conversation_id=tweet.get("conversation_id"),
                    created_at=datetime.fromisoformat(tweet["created_at"].replace('Z', '+00:00')),
                    referenced_tweets=tweet.get("referenced_tweets"),
                    context_annotations=tweet.get("context_annotations")
                )
                for tweet in data
            ]
                
        except Exception as e:
            logger.error(f"Error monitoring keywords: {str(e)}")
            return []
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit information from response headers."""
        try:
            url = f"{self.base_url}/tweets/search/recent"
            response = self.session.get(url, params={"query": "test", "max_results": 10})
            
            return {
                'resources': {
                    'tweets': {
                        '/tweets': {
                            'limit': int(response.headers.get('x-rate-limit-limit', 100)),
                            'remaining': int(response.headers.get('x-rate-limit-remaining', 50))
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limits: {str(e)}")
            return {}
    
    @property
    def state(self) -> XState:
        """Get current X state."""
        return self._state