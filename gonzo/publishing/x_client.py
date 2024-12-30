"""X (Twitter) API client implementation for Gonzo MVP."""
import os
import ssl
import certifi
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)

class XClient:
    """Simple async X (Twitter) v2 API client."""
    
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(self, 
                 api_key: str,
                 api_secret: str,
                 access_token: str,
                 access_token_secret: str,
                 wait_time: float = 1.0):
        """Initialize X client with API credentials."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.wait_time = wait_time
        self._bearer_token = None
        self._session = None
        
        # Create SSL context with certifi certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async def _get_oauth2_token(self) -> str:
        """Get OAuth 2.0 bearer token."""
        auth_url = "https://api.twitter.com/oauth2/token"
        auth = aiohttp.BasicAuth(self.api_key, self.api_secret)
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                auth_url,
                auth=auth,
                data={"grant_type": "client_credentials"}
            ) as response:
                data = await response.json()
                return data["access_token"]
    
    async def _ensure_session(self):
        """Ensure aiohttp session and bearer token exist."""
        if not self._session:
            if not self._bearer_token:
                self._bearer_token = await self._get_oauth2_token()
                
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self._session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "Authorization": f"Bearer {self._bearer_token}",
                    "Content-Type": "application/json"
                }
            )
    
    async def create_tweet(self, text: str, reply_to_id: str = None) -> Dict:
        """Create a tweet, optionally as a reply."""
        await self._ensure_session()
        
        data = {"text": text}
        if reply_to_id:
            data["reply"] = {"in_reply_to_tweet_id": reply_to_id}
            
        async with self._session.post(
            f"{self.BASE_URL}/tweets",
            json=data
        ) as response:
            return await response.json()
    
    async def create_thread(self, tweets: List[str]) -> List[Dict]:
        """Create a thread of tweets."""
        results = []
        previous_id = None
        
        for tweet in tweets:
            try:
                result = await self.create_tweet(tweet, previous_id)
                if "data" in result:
                    tweet_id = result["data"]["id"]
                    results.append({
                        "id": tweet_id,
                        "text": tweet,
                        "url": f"https://twitter.com/user/status/{tweet_id}"
                    })
                    previous_id = tweet_id
                else:
                    logger.error(f"Error creating tweet: {result}")
                    break
                    
                await asyncio.sleep(self.wait_time)
                
            except Exception as e:
                logger.error(f"Error in thread creation: {str(e)}")
                break
                
        return results
    
    @classmethod
    def from_env(cls, wait_time: float = 1.0) -> 'XClient':
        """Create client from environment variables."""
        required_vars = [
            'X_API_KEY',
            'X_API_SECRET',
            'X_ACCESS_TOKEN',
            'X_ACCESS_SECRET'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
            
        return cls(
            api_key=os.getenv('X_API_KEY'),
            api_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_SECRET'),
            wait_time=wait_time
        )