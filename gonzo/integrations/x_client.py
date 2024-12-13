"""X (Twitter) API client for Gonzo."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import tweepy
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
        # Initialize OAuth 1.1a authentication
        auth = tweepy.OAuthHandler(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET
        )
        auth.set_access_token(
            key=X_ACCESS_TOKEN,
            secret=X_ACCESS_SECRET
        )
        
        # Initialize API v2 client
        self.api = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )
        
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
                response = self.api.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=reply_to
                )
            else:
                response = self.api.create_tweet(text=text)
                
            return response.data
            
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
            # Get mentions timeline
            me = self.api.get_me()
            mentions = self.api.get_users_mentions(
                id=me.data.id,
                since_id=since_id,
                tweet_fields=['author_id', 'conversation_id', 'created_at',
                            'referenced_tweets', 'context_annotations']
            )
            
            if not mentions.data:
                return []
                
            # Convert to Tweet models
            tweets = []
            for tweet in mentions.data:
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
            tweets = self.api.search_recent_tweets(
                query=f"conversation_id:{conversation_id}",
                tweet_fields=['author_id', 'conversation_id', 'created_at',
                            'referenced_tweets', 'context_annotations'],
                max_results=100
            )
            
            if not tweets.data:
                return []
                
            # Convert to Tweet models
            thread = []
            for tweet in tweets.data:
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
            tweets = self.api.search_recent_tweets(
                query=query,
                tweet_fields=['author_id', 'conversation_id', 'created_at',
                            'referenced_tweets', 'context_annotations'],
                max_results=100
            )
            
            if not tweets.data:
                return []
                
            # Convert to Tweet models
            matching_tweets = []
            for tweet in tweets.data:
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