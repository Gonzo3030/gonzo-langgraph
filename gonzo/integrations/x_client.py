import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import requests
from requests_oauthlib import OAuth1Session

class RateLimitError(Exception):
    """Raised when X API rate limits are exceeded."""
    def __init__(self, message: str, reset_time: int):
        super().__init__(message)
        self.reset_time = reset_time

class AuthenticationError(Exception):
    """Raised when authentication with X API fails."""
    pass

class XClient:
    """Client for interacting with X API with OpenAPI integration."""
    
    def __init__(self, api_key: str, api_agent: Any):
        """Initialize X client with API key and OpenAPI agent.
        
        Args:
            api_key: X API authentication key
            api_agent: OpenAPI agent instance for API interactions
        """
        self.api_key = api_key
        self.api_agent = api_agent
        self._rate_limits: Dict[str, Dict[str, int]] = {
            "/tweets/search/recent": {"limit": 100, "remaining": 100, "reset": 0}
        }
        self._session = self._create_session()
    
    def _create_session(self) -> OAuth1Session:
        """Create authenticated OAuth session."""
        return OAuth1Session(
            self.api_key,
            client_secret=None,  # Will be loaded from config
            resource_owner_key=None,  # Will be loaded from config
            resource_owner_secret=None  # Will be loaded from config
        )
    
    def clear_cache(self) -> None:
        """Clear the OpenAPI agent cache."""
        self.api_agent.clear_cache('x')
    
    def health_check(self) -> bool:
        """Check if the API client is healthy and operational.
        
        Returns:
            bool: True if client is healthy and has available rate limits
        """
        try:
            limits = self.get_rate_limits()
            return any(limit.get('remaining', 0) > 0 for limit in limits.values())
        except Exception:
            return False
    
    def get_rate_limits(self) -> Dict[str, Dict[str, int]]:
        """Get current rate limits for the X API.
        
        Returns:
            Dict containing rate limit information for different endpoints
        """
        return self._rate_limits
    
    async def post_tweet(self, text: str, use_agent: bool = False) -> Dict[str, Any]:
        """Post a tweet using either OpenAPI agent or direct API call.
        
        Args:
            text: Tweet content
            use_agent: Whether to use OpenAPI agent (defaults to False)
            
        Returns:
            Dict containing tweet data
            
        Raises:
            RateLimitError: If rate limits are exceeded
            AuthenticationError: If authentication fails
        """
        if use_agent:
            try:
                return await self._post_tweet_with_agent(text)
            except Exception as e:
                # Fallback to direct request
                return await self._post_tweet_direct(text)
        return await self._post_tweet_direct(text)
    
    async def _post_tweet_with_agent(self, text: str) -> Dict[str, Any]:
        """Post tweet using OpenAPI agent."""
        response = await self.api_agent.query_api({
            "endpoint": "tweets",
            "method": "POST",
            "data": {"text": text}
        })
        return response
    
    async def _post_tweet_direct(self, text: str) -> Dict[str, Any]:
        """Post tweet using direct API call."""
        response = self._session.post(
            "https://api.twitter.com/2/tweets",
            json={"text": text}
        )
        
        if response.status_code == 429:
            reset_time = int(response.headers.get('x-rate-limit-reset', 0))
            raise RateLimitError("Rate limit exceeded", reset_time)
        elif response.status_code == 403:
            raise AuthenticationError("Authentication failed")
            
        return response.json()
    
    async def monitor_mentions(self, use_agent: bool = False) -> List[Dict[str, Any]]:
        """Monitor mentions using either OpenAPI agent or direct API call.
        
        Args:
            use_agent: Whether to use OpenAPI agent (defaults to False)
            
        Returns:
            List of mention data
        """
        if use_agent:
            try:
                return await self._monitor_mentions_with_agent()
            except Exception:
                return await self._monitor_mentions_direct()
        return await self._monitor_mentions_direct()
    
    async def _monitor_mentions_with_agent(self) -> List[Dict[str, Any]]:
        """Monitor mentions using OpenAPI agent."""
        # Get user ID first
        user_data = await self.api_agent.query_api({
            "endpoint": "users/me",
            "method": "GET"
        })
        
        # Then get mentions
        mentions = await self.api_agent.query_api({
            "endpoint": f"users/{user_data['id']}/mentions",
            "method": "GET"
        })
        return mentions.get('data', [])
    
    async def _monitor_mentions_direct(self) -> List[Dict[str, Any]]:
        """Monitor mentions using direct API call."""
        # Get user ID
        user_response = self._session.get(
            "https://api.twitter.com/2/users/me"
        )
        user_id = user_response.json()["data"]["id"]
        
        # Get mentions
        mentions_response = self._session.get(
            f"https://api.twitter.com/2/users/{user_id}/mentions"
        )
        return mentions_response.json().get('data', [])
    
    async def get_conversation_thread(
        self, tweet_id: str, use_agent: bool = False
    ) -> List[Dict[str, Any]]:
        """Get conversation thread for a tweet.
        
        Args:
            tweet_id: ID of the tweet to get conversation for
            use_agent: Whether to use OpenAPI agent (defaults to False)
            
        Returns:
            List of tweets in the conversation
        """
        if use_agent:
            try:
                return await self._get_thread_with_agent(tweet_id)
            except Exception:
                return await self._get_thread_direct(tweet_id)
        return await self._get_thread_direct(tweet_id)
    
    async def _get_thread_with_agent(self, tweet_id: str) -> List[Dict[str, Any]]:
        """Get conversation thread using OpenAPI agent."""
        response = await self.api_agent.query_api({
            "endpoint": f"tweets/{tweet_id}/conversation",
            "method": "GET"
        })
        return response.get('data', [])
    
    async def _get_thread_direct(self, tweet_id: str) -> List[Dict[str, Any]]:
        """Get conversation thread using direct API call."""
        response = self._session.get(
            f"https://api.twitter.com/2/tweets/{tweet_id}/conversation"
        )
        return response.json().get('data', [])
