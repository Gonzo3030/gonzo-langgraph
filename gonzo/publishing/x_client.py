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
    """X API client for posting threads."""
    
    BASE_URL = "https://api.twitter.com/2/tweets"
    
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
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        logger.info("Initialized X client")
    
    def _generate_auth_headers(self, method: str, url: str) -> Dict[str, str]:
        """Generate OAuth 1.0a headers according to X API v2 spec."""
        oauth_timestamp = str(int(time.time()))
        oauth_nonce = secrets.token_hex(16)
        
        # Create parameter string
        params = {
            'oauth_consumer_key': self.api_key,
            'oauth_nonce': oauth_nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': oauth_timestamp,
            'oauth_token': self.access_token,
            'oauth_version': '1.0'
        }
        
        # Sort and encode parameters
        param_string = '&'.join([
            f"{urllib.parse.quote(key)}={urllib.parse.quote(str(value))}"
            for key, value in sorted(params.items())
        ])
        
        # Create signature base string
        signature_base = '&'.join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_string, safe='')
        ])
        
        # Create signing key
        signing_key = f"{urllib.parse.quote(self.api_secret)}&{urllib.parse.quote(self.access_token_secret)}"
        
        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode('utf-8'),
                signature_base.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        # Add signature to parameters
        params['oauth_signature'] = signature
        
        # Create authorization header
        auth_header = 'OAuth ' + ', '.join([
            f"{urllib.parse.quote(key)}=\"{urllib.parse.quote(str(value))}\""
            for key, value in params.items()
        ])
        
        return {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
    
    async def create_tweet(self, text: str, reply_to_id: str = None) -> Dict:
        """Create a tweet, optionally as a reply."""
        data = {"text": text}
        if reply_to_id:
            data["reply"] = {"in_reply_to_tweet_id": reply_to_id}
        
        headers = self._generate_auth_headers('POST', self.BASE_URL)
        
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(self.BASE_URL, headers=headers, json=data) as response:
                    result = await response.json()
                    
                    if response.status == 201:
                        logger.info(f"Successfully created tweet")
                        return result
                    else:
                        logger.error(f"Error creating tweet: {result}")
                        return result
                    
        except Exception as e:
            error_msg = f"Error creating tweet: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    async def create_thread(self, tweets: List[str]) -> List[Dict]:
        """Create a thread of tweets."""
        results = []
        previous_id = None
        
        try:
            for i, tweet in enumerate(tweets):
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
                        logger.info(f"Posted tweet {i+1} of {len(tweets)}")
                    else:
                        logger.error(f"Failed to post tweet {i+1}: {result}")
                        break
                    
                    # Wait between tweets to respect rate limits
                    if i < len(tweets) - 1:
                        await asyncio.sleep(self.wait_time)
                        
                except Exception as e:
                    logger.error(f"Error in thread creation: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            
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