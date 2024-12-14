"""X (Twitter) API v2 client for Gonzo."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import requests
import logging
import time
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
    """Client for X API v2 interactions."""
    
    def __init__(self):
        """Initialize X client."""
        if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
            raise AuthenticationError("Missing required X API credentials")
            
        self.session = OAuth1Session(
            client_key=X_API_KEY,
            client_secret=X_API_SECRET,
            resource_owner_key=X_ACCESS_TOKEN,
            resource_owner_secret=X_ACCESS_SECRET
        )
        self.base_url = "https://api.twitter.com/2"
        self._state = XState()
        self.rate_limits = {}

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

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request with rate limit handling and retries."""
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

    async def post_tweet(self, text: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """Post a tweet with rate limit handling."""
        try:
            data = {"text": text}
            if reply_to:
                data["reply"] = {"in_reply_to_tweet_id": reply_to}
                
            response = await self._make_request(
                "POST",
                "/tweets",
                json=data
            )
            return response.json()["data"]
            
        except Exception as e:
            logger.error(f"Error posting tweet: {str(e)}")
            raise

    async def monitor_mentions(self, since_id: Optional[str] = None) -> List[Tweet]:
        """Monitor mentions of Gonzo."""
        try:
            # First get user ID
            me_response = await self._make_request("GET", "/users/me")
            user_id = me_response.json()["data"]["id"]
            
            # Get mentions
            params = {
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations"
            }
            if since_id:
                params["since_id"] = since_id
                
            response = await self._make_request(
                "GET",
                f"/users/{user_id}/mentions",
                params=params
            )
            data = response.json().get("data", [])
            
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
        """Get conversation thread."""
        try:
            params = {
                "query": f"conversation_id:{conversation_id}",
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations",
                "max_results": 100
            }
            
            response = await self._make_request(
                "GET",
                "/tweets/search/recent",
                params=params
            )
            data = response.json().get("data", [])
            
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
        """Monitor tweets containing keywords."""
        try:
            query = " OR ".join(keywords)
            params = {
                "query": query,
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations",
                "max_results": 100
            }
            if since_id:
                params["since_id"] = since_id
                
            response = await self._make_request(
                "GET",
                "/tweets/search/recent",
                params=params
            )
            data = response.json().get("data", [])
            
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
        """Get current rate limit information."""
        try:
            # Make a simple request to check rate limits
            endpoint = "/tweets/search/recent"
            params = {"query": "test", "max_results": 10}
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params)
            self._update_rate_limits(endpoint, response.headers)
            
            return self.rate_limits
            
        except Exception as e:
            logger.error(f"Error getting rate limits: {str(e)}")
            return {}

    @property
    def state(self) -> XState:
        """Get current X state."""
        return self._state
