"""X (Twitter) API client implementation."""
import os
import ssl
import hmac
import time
import base64
import certifi
import logging
import asyncio
import urllib.parse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import hashlib
import secrets

logger = logging.getLogger(__name__)

class XClient:
    """Wrapper for X API interactions with rate limiting."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        wait_time: float = 1.0
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.wait_time = wait_time
        self.last_request = datetime.min
        self._requests_remaining = 50  # X API default rate limit
        self._reset_time = datetime.now() + timedelta(minutes=15)
        
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
    
    async def _wait_for_rate_limit(self) -> None:
        """Handle rate limiting."""
        now = datetime.now()
        
        # Check if we need to wait for rate limit reset
        if self._requests_remaining <= 1:
            wait_seconds = (self._reset_time - now).total_seconds()
            if wait_seconds > 0:
                logger.warning(f"Rate limit reached, waiting {wait_seconds:.1f} seconds")
                await asyncio.sleep(wait_seconds)
                self._requests_remaining = 50
                self._reset_time = now + timedelta(minutes=15)
        
        # Always wait at least minimum wait_time between requests
        time_since_last = (now - self.last_request).total_seconds()
        if time_since_last < self.wait_time:
            await asyncio.sleep(self.wait_time - time_since_last)
        
        self.last_request = datetime.now()
        self._requests_remaining -= 1
    
    async def create_tweet(
        self,
        text: str,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a tweet with rate limiting."""
        url = 'https://api.twitter.com/2/tweets'
        
        data = {"text": text}
        if reply_to:
            data["reply"] = {"in_reply_to_tweet_id": reply_to}
        
        try:
            await self._wait_for_rate_limit()
            
            headers = self._generate_auth_headers('POST', url)
            logger.info(f"Generated headers for tweet")
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    status = response.status
                    
                    if status == 201 and 'data' in result:
                        logger.info("Successfully created tweet")
                        return {
                            'success': True,
                            'id': str(result['data']['id']),
                            'text': text
                        }
                    else:
                        raise ValueError(f"Error posting tweet: {result}")
                    
        except Exception as e:
            error_msg = f"Error creating tweet: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def create_thread(self, tweets: List[str]) -> List[Dict[str, Any]]:
        """Create a thread of tweets with rate limiting."""
        results = []
        reply_to = None
        
        for i, tweet in enumerate(tweets, 1):
            try:
                result = await self.create_tweet(tweet, reply_to)
                results.append(result)
                
                if result['success']:
                    reply_to = result['id']
                    logger.info(f"Posted tweet {i} of {len(tweets)}")
                    # Add extra delay between thread tweets
                    await asyncio.sleep(self.wait_time * 2)
                else:
                    logger.error(f"Failed to post tweet {i}: {result['error']}")
                    break
                    
            except Exception as e:
                error_msg = f"Error in thread at tweet {i}: {str(e)}"
                logger.error(error_msg)
                results.append({
                    'success': False,
                    'error': error_msg
                })
                break
        
        # Add longer delay after completing thread
        await asyncio.sleep(self.wait_time * 4)
        return results
    
    @classmethod
    def from_env(cls, wait_time: float = 1.0) -> 'XClient':
        """Create client from environment variables."""
        required = [
            'X_API_KEY',
            'X_API_SECRET',
            'X_ACCESS_TOKEN',
            'X_ACCESS_TOKEN_SECRET'  # Changed to match environment variable name
        ]
        
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        return cls(
            api_key=os.getenv('X_API_KEY'),
            api_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET')  # Changed to match
            wait_time=wait_time
        )