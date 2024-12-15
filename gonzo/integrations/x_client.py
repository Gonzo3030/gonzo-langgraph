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
    
    def _update_rate_limits(self, headers: Dict[str, str], endpoint: str) -> None:
        """Update rate limits from response headers."""
        self._rate_limits[endpoint] = {
            "limit": int(headers.get('x-rate-limit-limit', 0)),
            "remaining": int(headers.get('x-rate-limit-remaining', 0)),
            "reset": int(headers.get('x-rate-limit-reset', 0))
        }
    
    def _check_response(self, response: requests.Response, ignore_404: bool = False) -> None:
        """Check response for errors and update rate limits.
        
        Args:
            response: The response to check
            ignore_404: Whether to ignore 404 errors (useful for searches)
        """
        if response.status_code == 429:
            reset_time = int(response.headers.get('x-rate-limit-reset', 0))
            raise RateLimitError("Rate limit exceeded", reset_time)
        
        if response.status_code in (401, 403):
            raise AuthenticationError("Authentication failed")
            
        if response.status_code == 404 and not ignore_404:
            response.raise_for_status()
            
        if response.status_code >= 500:
            response.raise_for_status()
            
        # Update rate limits if available
        if 'x-rate-limit-remaining' in response.headers:
            self._update_rate_limits(response.headers, 
                                   response.request.path_url if response.request else '/tweets')
