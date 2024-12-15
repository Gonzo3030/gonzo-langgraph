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
        try:
            from gonzo.config.x import (
                X_API_SECRET,
                X_ACCESS_TOKEN,
                X_ACCESS_SECRET
            )
            return OAuth1Session(
                self.api_key,
                client_secret=X_API_SECRET,
                resource_owner_key=X_ACCESS_TOKEN,
                resource_owner_secret=X_ACCESS_SECRET
            )
        except ImportError:
            # For testing with mocked credentials
            return OAuth1Session(
                self.api_key,
                client_secret='test_secret',
                resource_owner_key='test_token',
                resource_owner_secret='test_secret'
            )
    
    def clear_cache(self) -> None:
        """Clear the OpenAPI agent cache."""
        if hasattr(self.api_agent, 'clear_cache'):
            self.api_agent.clear_cache('x')
    
    def health_check(self) -> bool:
        """Check if the API client is healthy and operational."""
        try:
            limits = self.get_rate_limits()
            return any(
                limit.get('remaining', 0) > 0 
                for limit in limits.values()
            )
        except Exception:
            return False
    
    def get_rate_limits(self) -> Dict[str, Dict[str, int]]:
        """Get current rate limits for the X API."""
        if hasattr(self.api_agent, 'rate_limits'):
            return self.api_agent.rate_limits
        return self._rate_limits
    
    async def post_tweet(self, text: str, use_agent: bool = False) -> Dict[str, Any]:
        """Post a tweet using either OpenAPI agent or direct API call."""
        if use_agent:
            try:
                return await self._post_tweet_with_agent(text)
            except Exception as e:
                return await self._post_tweet_direct(text)
        return await self._post_tweet_direct(text)
    
    async def _post_tweet_with_agent(self, text: str) -> Dict[str, Any]:
        """Post tweet using OpenAPI agent."""
        response = self.api_agent.query_api({
            "endpoint": "tweets",
            "method": "POST",
            "data": {"text": text}
        })
        if asyncio.iscoroutine(response):
            response = await response
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
        """Monitor mentions using either OpenAPI agent or direct API call."""
        if use_agent:
            try:
                return await self._monitor_mentions_with_agent()
            except Exception:
                return await self._monitor_mentions_direct()
        return await self._monitor_mentions_direct()
    
    async def _monitor_mentions_with_agent(self) -> List[Dict[str, Any]]:
        """Monitor mentions using OpenAPI agent."""
        # Get user ID first
        user_data = self.api_agent.query_api({
            "endpoint": "users/me",
            "method": "GET"
        })
        if asyncio.iscoroutine(user_data):
            user_data = await user_data
        
        # Then get mentions
        mentions = self.api_agent.query_api({
            "endpoint": f"users/{user_data['data']['id']}/mentions",
            "method": "GET"
        })
        if asyncio.iscoroutine(mentions):
            mentions = await mentions
        return mentions.get('data', [])
    
    async def _monitor_mentions_direct(self) -> List[Dict[str, Any]]:
        """Monitor mentions using direct API call."""
        # Get user ID
        user_response = self._session.get(
            "https://api.twitter.com/2/users/me"
        )
        if user_response.status_code != 200:
            return []

        try:
            user_id = user_response.json()["data"]["id"]
        except (KeyError, ValueError):
            return []
        
        # Get mentions
        mentions_response = self._session.get(
            f"https://api.twitter.com/2/users/{user_id}/mentions"
        )
        if mentions_response.status_code != 200:
            return []
            
        try:
            return mentions_response.json().get('data', [])
        except ValueError:
            return []
    
    async def get_conversation_thread(
        self, tweet_id: str, use_agent: bool = False
    ) -> List[Dict[str, Any]]:
        """Get conversation thread for a tweet."""
        if use_agent:
            try:
                return await self._get_thread_with_agent(tweet_id)
            except Exception:
                return await self._get_thread_direct(tweet_id)
        return await self._get_thread_direct(tweet_id)
    
    async def _get_thread_with_agent(self, tweet_id: str) -> List[Dict[str, Any]]:
        """Get conversation thread using OpenAPI agent."""
        response = self.api_agent.query_api({
            "endpoint": f"tweets/{tweet_id}/conversation",
            "method": "GET"
        })
        if asyncio.iscoroutine(response):
            response = await response
        return response.get('data', [])
    
    async def _get_thread_direct(self, tweet_id: str) -> List[Dict[str, Any]]:
        """Get conversation thread using direct API call."""
        response = self._session.get(
            f"https://api.twitter.com/2/tweets/{tweet_id}/conversation"
        )
        if response.status_code != 200:
            return []
            
        try:
            return response.json().get('data', [])
        except ValueError:
            return []