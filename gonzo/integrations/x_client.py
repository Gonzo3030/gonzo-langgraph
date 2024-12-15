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
        """Initialize X client with API key and OpenAPI agent."""
        self.api_key = api_key
        self.api_agent = api_agent
        self._rate_limits: Dict[str, Dict[str, int]] = {
            "/tweets/search/recent": {"limit": 100, "remaining": 100, "reset": 0}
        }
        self._session = None
    
    @property
    def session(self) -> OAuth1Session:
        """Get or create OAuth session."""
        if self._session is None:
            self._session = self._create_session()
        return self._session
    
    def _create_session(self) -> OAuth1Session:
        """Create authenticated OAuth session."""
        try:
            from gonzo.config.x import (
                X_API_SECRET,
                X_ACCESS_TOKEN,
                X_ACCESS_SECRET
            )
            session = OAuth1Session(
                self.api_key,
                client_secret=X_API_SECRET,
                resource_owner_key=X_ACCESS_TOKEN,
                resource_owner_secret=X_ACCESS_SECRET
            )
        except ImportError:
            session = OAuth1Session(
                self.api_key,
                client_secret='test_secret',
                resource_owner_key='test_token',
                resource_owner_secret='test_secret'
            )
        return session
    
    def _update_rate_limits(self, headers: Dict[str, str], endpoint: str) -> None:
        """Update rate limits from response headers."""
        self._rate_limits[endpoint] = {
            "limit": int(headers.get('x-rate-limit-limit', 0)),
            "remaining": int(headers.get('x-rate-limit-remaining', 0)),
            "reset": int(headers.get('x-rate-limit-reset', 0))
        }
    
    def _check_response(self, response: requests.Response, ignore_404: bool = False) -> Dict[str, Any]:
        """Check response for errors and update rate limits.
        
        Args:
            response: The response to check
            ignore_404: Whether to ignore 404 errors (useful for searches)
            
        Returns:
            Dict containing the JSON response data
        """
        if 'x-rate-limit-remaining' in response.headers:
            self._update_rate_limits(response.headers, 
                                   response.request.path_url if response.request else '/tweets')

        if response.status_code == 429:
            reset_time = int(response.headers.get('x-rate-limit-reset', 0))
            raise RateLimitError("Rate limit exceeded", reset_time)
            
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
            
        if response.status_code == 403:
            raise AuthenticationError("Forbidden - Check credentials")
            
        if response.status_code == 404 and not ignore_404:
            response.raise_for_status()
            
        if response.status_code >= 500:
            response.raise_for_status()
            
        if not 200 <= response.status_code < 300:
            response.raise_for_status()
            
        return response.json()
    
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
            return getattr(self.api_agent, 'rate_limits')
        return self._rate_limits
    
    async def post_tweet(self, text: str, use_agent: bool = False) -> Dict[str, Any]:
        """Post a tweet using either OpenAPI agent or direct API call."""
        try:
            if use_agent:
                try:
                    return await self._post_tweet_with_agent(text)
                except Exception as e:
                    if isinstance(e, (RateLimitError, AuthenticationError)):
                        raise
            return await self._post_tweet_direct(text)
        except Exception as e:
            if isinstance(e, (RateLimitError, AuthenticationError)):
                raise
            raise RuntimeError(f"Failed to post tweet: {str(e)}")
    
    async def _post_tweet_with_agent(self, text: str) -> Dict[str, Any]:
        """Post tweet using OpenAPI agent."""
        response = self.api_agent.query_api({
            "endpoint": "tweets",
            "method": "POST",
            "data": {"text": text}
        })
        if asyncio.iscoroutine(response):
            response = await response
        return response.get('data', {})
    
    async def _post_tweet_direct(self, text: str) -> Dict[str, Any]:
        """Post tweet using direct API call."""
        response = self.session.post(
            "https://api.twitter.com/2/tweets",
            json={"text": text}
        )
        
        response_data = self._check_response(response)
        return response_data.get('data', {})
    
    async def monitor_mentions(self, use_agent: bool = False) -> List[Dict[str, Any]]:
        """Monitor mentions using either OpenAPI agent or direct API call."""
        try:
            if use_agent:
                try:
                    return await self._monitor_mentions_with_agent()
                except Exception as e:
                    if isinstance(e, (RateLimitError, AuthenticationError)):
                        raise
            return await self._monitor_mentions_direct()
        except Exception as e:
            if isinstance(e, (RateLimitError, AuthenticationError)):
                raise
            return []
    
    async def _monitor_mentions_with_agent(self) -> List[Dict[str, Any]]:
        """Monitor mentions using OpenAPI agent."""
        user_data = self.api_agent.query_api({
            "endpoint": "users/me",
            "method": "GET"
        })
        if asyncio.iscoroutine(user_data):
            user_data = await user_data
        
        mentions = self.api_agent.query_api({
            "endpoint": f"users/{user_data['data']['id']}/mentions",
            "method": "GET"
        })
        if asyncio.iscoroutine(mentions):
            mentions = await mentions
        return mentions.get('data', [])
    
    async def _monitor_mentions_direct(self) -> List[Dict[str, Any]]:
        """Monitor mentions using direct API call."""
        user_response = self.session.get(
            "https://api.twitter.com/2/users/me"
        )
        user_data = self._check_response(user_response)
        
        mentions_response = self.session.get(
            f"https://api.twitter.com/2/users/{user_data['data']['id']}/mentions"
        )
        mentions_data = self._check_response(mentions_response)
        return mentions_data.get('data', [])
    
    async def get_conversation_thread(
        self, tweet_id: str, use_agent: bool = False
    ) -> List[Dict[str, Any]]:
        """Get conversation thread for a tweet."""
        try:
            if use_agent:
                try:
                    return await self._get_thread_with_agent(tweet_id)
                except Exception as e:
                    if isinstance(e, (RateLimitError, AuthenticationError)):
                        raise
            return await self._get_thread_direct(tweet_id)
        except Exception as e:
            if isinstance(e, (RateLimitError, AuthenticationError)):
                raise
            return []
    
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
        response = self.session.get(
            f"https://api.twitter.com/2/tweets/{tweet_id}/conversation"
        )
        response_data = self._check_response(response)
        return response_data.get('data', [])