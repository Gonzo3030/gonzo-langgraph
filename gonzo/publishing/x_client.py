"""X (Twitter) API client implementation with enhanced tweet limit handling."""
import os
import ssl
import hmac
import time
import json
import base64
import certifi
import logging
import asyncio
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import aiohttp
import hashlib
import secrets

logger = logging.getLogger(__name__)

class TweetLimit:
    """Track and manage tweet limits."""
    
    def __init__(self, headers: Dict[str, str]):
        """Initialize from API response headers."""
        self.app_limit = int(headers.get('x-app-limit-24hour-limit', '17'))
        self.app_remaining = int(headers.get('x-app-limit-24hour-remaining', '0'))
        self.user_limit = int(headers.get('x-user-limit-24hour-limit', '17'))
        self.user_remaining = int(headers.get('x-user-limit-24hour-remaining', '0'))
        self.reset_timestamp = int(headers.get('x-app-limit-24hour-reset', '0'))
        
    @property
    def can_tweet(self) -> bool:
        """Check if tweeting is allowed."""
        return self.app_remaining > 0 and self.user_remaining > 0
    
    @property
    def wait_seconds(self) -> int:
        """Calculate seconds until reset."""
        now = int(datetime.now(timezone.utc).timestamp())
        return max(0, self.reset_timestamp - now)
    
    @property
    def reset_time(self) -> datetime:
        """Get reset time as datetime."""
        return datetime.fromtimestamp(self.reset_timestamp, timezone.utc)
    
    def __str__(self) -> str:
        """Human readable limit status."""
        reset_time_str = self.reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        return (
            f"Tweet Limits:\n"
            f"  App:  {self.app_remaining}/{self.app_limit} remaining\n"
            f"  User: {self.user_remaining}/{self.user_limit} remaining\n"
            f"  Resets at: {reset_time_str}\n"
            f"  Wait time: {self.wait_seconds//3600}h {(self.wait_seconds%3600)//60}m"
        )

class XClient:
    """Wrapper for X API interactions with enhanced limit handling."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        wait_time: float = 3.0,  # 3s between tweets in a thread
        max_retries: int = 3,
        initial_wait: float = 5.0  # 5s before starting thread
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.wait_time = wait_time
        self.max_retries = max_retries
        self.initial_wait = initial_wait
        self.last_tweet_time = None
        self._first_tweet = True
        self.tweet_limit: Optional[TweetLimit] = None
        logger.info(f"Initialized X client (wait_time={wait_time}s, initial_wait={initial_wait}s)")
    
    def _generate_auth_headers(self, method: str, url: str) -> Dict[str, str]:
        """Generate OAuth 1.0a headers according to X API v2 spec."""
        oauth_timestamp = str(int(time.time()))
        oauth_nonce = secrets.token_hex(16)
        
        params = {
            'oauth_consumer_key': self.api_key,
            'oauth_nonce': oauth_nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': oauth_timestamp,
            'oauth_token': self.access_token,
            'oauth_version': '1.0'
        }
        
        param_string = '&'.join([
            f"{urllib.parse.quote(key)}={urllib.parse.quote(str(value))}"
            for key, value in sorted(params.items())
        ])
        
        signature_base = '&'.join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_string, safe='')
        ])
        
        signing_key = f"{urllib.parse.quote(self.api_secret)}&{urllib.parse.quote(self.access_token_secret)}"
        
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode('utf-8'),
                signature_base.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        params['oauth_signature'] = signature
        
        auth_header = 'OAuth ' + ', '.join([
            f"{urllib.parse.quote(key)}=\"{urllib.parse.quote(str(value))}\""
            for key, value in params.items()
        ])
        
        return {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
    
    async def _wait_for_rate_limit(self) -> None:
        """Ensure proper spacing between tweets."""
        if self._first_tweet:
            logger.info(f"Initial wait of {self.initial_wait}s before starting thread...")
            await asyncio.sleep(self.initial_wait)
            self._first_tweet = False
            return

        now = datetime.now()
        if self.last_tweet_time:
            elapsed = (now - self.last_tweet_time).total_seconds()
            if elapsed < self.wait_time:
                wait_time = self.wait_time - elapsed
                logger.info(f"Waiting {wait_time:.1f}s before next tweet in thread...")
                await asyncio.sleep(wait_time)
    
    def _update_tweet_limit(self, headers: Dict[str, str]):
        """Update tweet limit tracking from response headers."""
        self.tweet_limit = TweetLimit(headers)
        if not self.tweet_limit.can_tweet:
            logger.warning(str(self.tweet_limit))
    
    async def create_tweet(
        self,
        text: str,
        reply_to: Optional[str] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Create a tweet with enhanced limit handling."""
        try:
            # Check existing limit before attempting
            if self.tweet_limit and not self.tweet_limit.can_tweet:
                wait_time = self.tweet_limit.wait_seconds
                if wait_time > 0:
                    error_msg = (
                        f"Tweet limit reached. Must wait {wait_time//3600}h "
                        f"{(wait_time%3600)//60}m until {self.tweet_limit.reset_time}"
                    )
                    logger.error(error_msg)
                    return {
                        'success': False,
                        'error': error_msg,
                        'limit_info': str(self.tweet_limit)
                    }
            
            await self._wait_for_rate_limit()
            
            url = 'https://api.twitter.com/2/tweets'
            data = {"text": text}
            if reply_to:
                data["reply"] = {"in_reply_to_tweet_id": reply_to}
            
            headers = self._generate_auth_headers('POST', url)
            logger.info("Attempting to post tweet...")
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    status = response.status
                    response_headers = dict(response.headers)
                    
                    # Always update limit tracking
                    self._update_tweet_limit(response_headers)
                    
                    if status == 201 and 'data' in result:
                        logger.info("Successfully posted tweet")
                        self.last_tweet_time = datetime.now()
                        return {
                            'success': True,
                            'id': str(result['data']['id']),
                            'text': text,
                            'limit_info': str(self.tweet_limit)
                        }
                    elif status == 429:  # Rate/Tweet limit
                        error_msg = f"Tweet limit reached: {result.get('detail', 'Unknown error')}"
                        logger.error(error_msg)
                        return {
                            'success': False,
                            'error': error_msg,
                            'limit_info': str(self.tweet_limit),
                            'reset_time': self.tweet_limit.reset_time if self.tweet_limit else None
                        }
                    else:
                        error_msg = f"Error posting tweet: {result}"
                        logger.error(error_msg)
                        return {
                            'success': False,
                            'error': result,
                            'status': status,
                            'headers': response_headers,
                            'limit_info': str(self.tweet_limit)
                        }
                    
        except Exception as e:
            error_msg = f"Error creating tweet: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def get_tweet_limit(self) -> Optional[TweetLimit]:
        """Get current tweet limit status."""
        try:
            # Make a minimal API call to get limit headers
            url = 'https://api.twitter.com/2/users/me'
            headers = self._generate_auth_headers('GET', url)
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers) as response:
                    self._update_tweet_limit(dict(response.headers))
                    return self.tweet_limit
                    
        except Exception as e:
            logger.error(f"Error getting tweet limit: {str(e)}")
            return None
    
    @classmethod
    def from_env(cls, wait_time: float = 3.0) -> 'XClient':
        """Create client from environment variables."""
        required = [
            'X_API_KEY',
            'X_API_SECRET',
            'X_ACCESS_TOKEN',
            'X_ACCESS_SECRET'
        ]
        
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        return cls(
            api_key=os.getenv('X_API_KEY'),
            api_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_SECRET'),
            wait_time=wait_time
        )
