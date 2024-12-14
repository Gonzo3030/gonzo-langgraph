"""X (Twitter) API v2 client for Gonzo using OpenAPI integration."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import requests
import logging
import time
from pathlib import Path
from requests_oauthlib import OAuth1Session
from pydantic import BaseModel

from ..config.x import (
    X_API_KEY,
    X_API_SECRET,
    X_ACCESS_TOKEN,
    X_ACCESS_SECRET,
    X_MAX_RETRIES,
    X_BASE_DELAY,
    X_MAX_DELAY
)
from ..state.x_state import XState
from ..api.openapi_agent import OpenAPIAgentTool

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Custom exception for rate limit handling."""
    def __init__(self, message: str, reset_time: Optional[int] = None):
        super().__init__(message)
        self.reset_time = reset_time

class AuthenticationError(Exception):
    """Custom exception for authentication issues."""
    pass

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
    """Client for X API v2 interactions with OpenAPI integration."""
    
    def __init__(self, llm, spec_path: Optional[str] = None):
        """Initialize X client with OpenAPI support.
        
        Args:
            llm: Language model for OpenAPI agent
            spec_path: Path to OpenAPI spec file (defaults to package location)
        """
        if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
            raise AuthenticationError("Missing required X API credentials")

        # Initialize standard OAuth session
        self.session = OAuth1Session(
            client_key=X_API_KEY,
            client_secret=X_API_SECRET,
            resource_owner_key=X_ACCESS_TOKEN,
            resource_owner_secret=X_ACCESS_SECRET
        )
        self.base_url = "https://api.twitter.com/2"
        
        # Initialize state tracking
        self._state = XState()
        self.rate_limits = {}
        
        # Initialize OpenAPI agent
        if spec_path is None:
            spec_path = str(Path(__file__).parent.parent / 'api' / 'specs' / 'x_api.yaml')
        
        self.api_agent = OpenAPIAgentTool(
            llm=llm,
            cache_duration=300,  # 5 minutes
            max_retries=X_MAX_RETRIES
        )
        self.api_agent.create_agent_for_api(spec_path, 'x')
        self.api_agent.add_rate_limit('x', X_BASE_DELAY)

    def _calculate_wait_time(self, headers: Dict[str, str], attempt: int) -> float:
        """Calculate wait time based on rate limit headers and retry attempt."""
        reset_time = int(headers.get('x-rate-limit-reset', 0))
        if reset_time:
            wait_time = max(reset_time - time.time(), 0)
        else:
            wait_time = min(X_BASE_DELAY * (2 ** attempt), X_MAX_DELAY)
        return wait_time

    def _update_rate_limits(self, endpoint: str, headers: Dict[str, str]):
        """Update rate limit information for an endpoint."""
        if all(key in headers for key in ['x-rate-limit-limit', 'x-rate-limit-remaining', 'x-rate-limit-reset']):
            self.rate_limits[endpoint] = {
                'limit': int(headers['x-rate-limit-limit']),
                'remaining': int(headers['x-rate-limit-remaining']),
                'reset': int(headers['x-rate-limit-reset'])
            }
            # Update OpenAPI agent rate limits
            self.api_agent.add_rate_limit('x', int(headers['x-rate-limit-reset']) - int(time.time()))

    async def _make_request(self, method: str, endpoint: str, use_agent: bool = False, **kwargs) -> Any:
        """Make an API request with rate limit handling and retries.
        
        Args:
            method: HTTP method to use
            endpoint: API endpoint to call
            use_agent: Whether to use OpenAPI agent instead of direct request
            **kwargs: Additional arguments for request
        """
        if use_agent:
            try:
                return await self.api_agent.query_api('x', f"{method} {endpoint} {kwargs}")
            except Exception as e:
                logger.error(f"OpenAPI agent error: {str(e)}")
                # Fall back to direct request
                logger.info("Falling back to direct request")

        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(X_MAX_RETRIES):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, **kwargs)
                else:
                    response = self.session.post(url, **kwargs)
                
                self._update_rate_limits(endpoint, response.headers)
                
                if response.status_code == 429:
                    wait_time = self._calculate_wait_time(response.headers, attempt)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    
                    if attempt == X_MAX_RETRIES - 1:
                        raise RateLimitError(
                            f"Rate limit exceeded for {endpoint}",
                            reset_time=int(response.headers.get('x-rate-limit-reset', 0))
                        )
                        
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 403:
                    raise AuthenticationError(f"Authentication failed for {endpoint}: {response.text}")
                    
                response.raise_for_status()
                return response
                
            except (requests.exceptions.RequestException, AuthenticationError) as e:
                if attempt == X_MAX_RETRIES - 1:
                    raise
                    
                wait_time = min(X_BASE_DELAY * (2 ** attempt), X_MAX_DELAY)
                logger.warning(f"Request failed. Retrying in {wait_time} seconds... Error: {str(e)}")
                time.sleep(wait_time)
        
        raise Exception(f"Max retries ({X_MAX_RETRIES}) exceeded for {endpoint}")
