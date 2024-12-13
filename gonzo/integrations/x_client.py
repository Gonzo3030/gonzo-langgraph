"""X (Twitter) API client for Gonzo."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from twitter.account import Account
from twitter.client import Client
from twitter.tweet import Tweet as TwitterTweet
import logging
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
    """Client for X API interactions."""
    
    def __init__(self):
        """Initialize X client."""
        # Initialize API v2 client
        self.client = Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            token=X_ACCESS_TOKEN,
            token_secret=X_ACCESS_SECRET
        )
        
        # Initialize account
        self.account = Account(client=self.client)
        
        # Initialize state
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
            if reply_to:
                tweet = self.account.tweet(text=text, reply_to=reply_to)
            else:
                tweet = self.account.tweet(text=text)
                
            return tweet.__dict__
            
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
            # Get mentions
            mentions = self.account.mentions(since_id=since_id)
            
            if not mentions:
                return []
                
            # Convert to Tweet models
            tweets = []
            for tweet in mentions:
                tweets.append(Tweet(
                    id=tweet.id,
                    text=tweet.text,
                    author_id=tweet.author_id,
                    conversation_id=tweet.conversation_id,
                    created_at=tweet.created_at,
                    referenced_tweets=tweet.referenced_tweets,
                    context_annotations=tweet.context_annotations
                ))
                
            return tweets
                
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
            # Get conversation tweets
            tweets = self.client.search_tweets(
                f"conversation_id:{conversation_id}",
                max_results=100
            )
            
            if not tweets:
                return []
                
            # Convert to Tweet models
            thread = []
            for tweet in tweets:
                thread.append(Tweet(
                    id=tweet.id,
                    text=tweet.text,
                    author_id=tweet.author_id,
                    conversation_id=tweet.conversation_id,
                    created_at=tweet.created_at,
                    referenced_tweets=tweet.referenced_tweets,
                    context_annotations=tweet.context_annotations
                ))
                
            return sorted(thread, key=lambda x: x.created_at)
                
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
            query = " OR ".join(keywords)
            
            # Search tweets
            tweets = self.client.search_tweets(
                query=query,
                since_id=since_id,
                max_results=100
            )
            
            if not tweets:
                return []
                
            # Convert to Tweet models
            matching_tweets = []
            for tweet in tweets:
                matching_tweets.append(Tweet(
                    id=tweet.id,
                    text=tweet.text,
                    author_id=tweet.author_id,
                    conversation_id=tweet.conversation_id,
                    created_at=tweet.created_at,
                    referenced_tweets=tweet.referenced_tweets,
                    context_annotations=tweet.context_annotations
                ))
                
            return matching_tweets
                
        except Exception as e:
            logger.error(f"Error monitoring keywords: {str(e)}")
            return []
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit information."""
        try:
            return {
                'resources': {
                    'tweets': {
                        '/tweets': {
                            'limit': 100,
                            'remaining': 50
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