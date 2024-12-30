"""X (Twitter) API client implementation for Gonzo MVP."""
import os
import ssl
import hmac
import time
import base64
import certifi
import logging
import asyncio
import urllib.parse
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
import hashlib
import secrets

logger = logging.getLogger(__name__)

class XClient:
    """Simple async X (Twitter) v2 API client using OAuth 1.0a."""
    
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
        self._session = None
        
        # Create SSL context with certifi certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str]) -> str:
        """Generate OAuth 1.0a signature."""
        # Collect parameters
        oauth_params = {
            'oauth_consumer_key': self.api_key,
            'oauth_nonce': secrets.token_hex(16),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': self.access_token,
            'oauth_version': '1.0'
        }
        
        # Combine all parameters
        all_params = {**params, **oauth_params}
        
        # Create parameter string
        param_string = '&'.join([
            f"{urllib.parse.quote(key)}={urllib.parse.quote(str(value))}"
            for key, value in sorted(all_params.items())
        ])
        
        # Create signature base string
        signature_base = '&'.join([
            method,
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_string, safe='')
        ])
        
        # Create signing key
        signing_key = '&'.join([
            urllib.parse.quote(self.api_secret, safe=''),
            urllib.parse.quote(self.access_token_secret, safe='')
        ])
        
        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode('utf-8'),
                signature_base.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return signature
    
    def _get_oauth_header(self, method: str, url: str, params: Dict[str, str] = None) -> str:
        """Get OAuth 1.0a Authorization header."""
        params = params or {}
        
        oauth_params = {
            'oauth_consumer_key': self.api_key,
            'oauth_nonce': secrets.token_hex(16),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': self.access_token,
            'oauth_version': '1.0'
        }
        
        # Generate signature
        oauth_params['oauth_signature'] = self._generate_oauth_signature(method, url, {**params, **oauth_params})
        
        # Create authorization header
        return 'OAuth ' + ', '.join([
            f'{urllib.parse.quote(key)}="{urllib.parse.quote(str(value))}"'
            for key, value in oauth_params.items()
        ])
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self._session:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self._session = aiohttp.ClientSession(connector=connector)
    
    async def create_tweet(self, text: str, reply_to_id: str = None) -> Dict:
        """Create a tweet, optionally as a reply."""
        await self._ensure_session()
        
        url = f"{self.BASE_URL}/tweets"
        data = {"text": text}
        if reply_to_id:
            data["reply"] = {"in_reply_to_tweet_id": reply_to_id}
        
        headers = {
            'Authorization': self._get_oauth_header('POST', url),
            'Content-Type': 'application/json'
        }
        
        async with self._session.post(url, headers=headers, json=data) as response:
            result = await response.json()
            if response.status != 201:
                logger.error(f"Error creating tweet: {result}")
            return result
    
    async def create_thread(self, tweets: List[str]) -> List[Dict]:
        """Create a thread of tweets."""
        results = []
        previous_id = None
        
        try:
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
                        logger.info(f"Successfully posted tweet: {tweet_id}")
                    else:
                        logger.error(f"Error creating tweet: {result}")
                        break
                        
                    await asyncio.sleep(self.wait_time)
                    
                except Exception as e:
                    logger.error(f"Error posting tweet: {str(e)}")
                    break
                    
        finally:
            # Clean up session
            if self._session:
                await self._session.close()
                self._session = None
        
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