"""X (Twitter) API v2 client implementation."""
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
import asyncio
from dataclasses import dataclass

@dataclass
class Tweet:
    id: str
    text: str
    author_id: str
    created_at: datetime
    public_metrics: Dict[str, int]

class RateLimitError(Exception):
    """Custom exception for rate limit handling"""
    def __init__(self, reset_time: datetime, remaining: int):
        self.reset_time = reset_time
        self.remaining = remaining
        super().__init__(f"Rate limit reached. Resets at {reset_time}. {remaining} requests remaining.")

class XClient:
    """X (Twitter) API v2 client with rate limiting."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.base_url = "https://api.twitter.com/2"
        self.last_request_time = None
        self.min_request_interval = 1.1  # Minimum seconds between requests
        
        # Get bearer token
        self.bearer_token = self._get_bearer_token()
    
    def _get_bearer_token(self) -> str:
        """Get bearer token using app credentials."""
        url = "https://api.twitter.com/oauth2/token"
        auth = (self.api_key, self.api_secret)
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(url, auth=auth, data=data)
        response.raise_for_status()
        
        return response.json()['access_token']
    
    async def _enforce_rate_limit(self):
        """Enforce minimum time between requests."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = datetime.now()
    
    def _parse_rate_limits(self, headers: Dict[str, str]) -> Tuple[int, datetime]:
        """Parse rate limit headers."""
        remaining = int(headers.get('x-rate-limit-remaining', 0))
        reset_time = datetime.fromtimestamp(
            int(headers.get('x-rate-limit-reset', 0))
        )
        return remaining, reset_time
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int, datetime]:
        """Make authenticated request to X API with rate limiting."""
        await self._enforce_rate_limit()
        
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        
        # Parse rate limits
        remaining, reset_time = self._parse_rate_limits(response.headers)
        
        if response.status_code == 429:
            raise RateLimitError(reset_time, remaining)
            
        response.raise_for_status()
        return response.json(), remaining, reset_time
    
    async def search_recent(self, query: str, max_results: int = 10) -> Tuple[List[Tweet], int, datetime]:
        """Search recent tweets."""
        endpoint = "tweets/search/recent"
        params = {
            'query': query,
            'max_results': max_results,
            'tweet.fields': 'created_at,public_metrics,author_id'
        }
        
        response_data, remaining, reset_time = await self._make_request(endpoint, params)
        tweets = []
        
        if 'data' in response_data:
            for tweet_data in response_data['data']:
                tweets.append(Tweet(
                    id=tweet_data['id'],
                    text=tweet_data['text'],
                    author_id=tweet_data['author_id'],
                    created_at=datetime.fromisoformat(tweet_data['created_at'].replace('Z', '+00:00')),
                    public_metrics=tweet_data.get('public_metrics', {})
                ))
        
        return tweets, remaining, reset_time
    
    async def get_user_tweets(self, user_id: str, max_results: int = 10) -> Tuple[List[Tweet], int, datetime]:
        """Get tweets from a specific user."""
        endpoint = f"users/{user_id}/tweets"
        params = {
            'max_results': max_results,
            'tweet.fields': 'created_at,public_metrics'
        }
        
        response_data, remaining, reset_time = await self._make_request(endpoint, params)
        tweets = []
        
        if 'data' in response_data:
            for tweet_data in response_data['data']:
                tweets.append(Tweet(
                    id=tweet_data['id'],
                    text=tweet_data['text'],
                    author_id=user_id,
                    created_at=datetime.fromisoformat(tweet_data['created_at'].replace('Z', '+00:00')),
                    public_metrics=tweet_data.get('public_metrics', {})
                ))
        
        return tweets, remaining, reset_time
    
    async def get_user_by_username(self, username: str) -> Tuple[Optional[Dict[str, Any]], int, datetime]:
        """Get user information by username."""
        endpoint = f"users/by/username/{username}"
        
        try:
            response_data, remaining, reset_time = await self._make_request(endpoint)
            return response_data.get('data'), remaining, reset_time
        except RateLimitError as e:
            raise
        except Exception:
            return None, 0, datetime.now()