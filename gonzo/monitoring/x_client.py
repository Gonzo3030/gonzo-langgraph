"""X (Twitter) API v2 client implementation."""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
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

class XClient:
    """Simple X (Twitter) API v2 client without tweepy dependency."""
    
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
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to X API."""
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def search_recent(self, query: str, max_results: int = 10) -> List[Tweet]:
        """Search recent tweets."""
        endpoint = "tweets/search/recent"
        params = {
            'query': query,
            'max_results': max_results,
            'tweet.fields': 'created_at,public_metrics,author_id'
        }
        
        response = self._make_request(endpoint, params)
        tweets = []
        
        if 'data' in response:
            for tweet_data in response['data']:
                tweets.append(Tweet(
                    id=tweet_data['id'],
                    text=tweet_data['text'],
                    author_id=tweet_data['author_id'],
                    created_at=datetime.fromisoformat(tweet_data['created_at'].replace('Z', '+00:00')),
                    public_metrics=tweet_data.get('public_metrics', {})
                ))
        
        return tweets
    
    def get_user_tweets(self, user_id: str, max_results: int = 10) -> List[Tweet]:
        """Get tweets from a specific user."""
        endpoint = f"users/{user_id}/tweets"
        params = {
            'max_results': max_results,
            'tweet.fields': 'created_at,public_metrics'
        }
        
        response = self._make_request(endpoint, params)
        tweets = []
        
        if 'data' in response:
            for tweet_data in response['data']:
                tweets.append(Tweet(
                    id=tweet_data['id'],
                    text=tweet_data['text'],
                    author_id=user_id,
                    created_at=datetime.fromisoformat(tweet_data['created_at'].replace('Z', '+00:00')),
                    public_metrics=tweet_data.get('public_metrics', {})
                ))
        
        return tweets
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information by username."""
        endpoint = f"users/by/username/{username}"
        
        try:
            response = self._make_request(endpoint)
            return response.get('data')
        except:
            return None