"""X (Twitter) API client implementation."""
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
from typing import Dict, List, Any, Optional
from datetime import datetime
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
        wait_time: float = 60.0,  # Default 1 minute between tweets
        max_retries: int = 3,
        initial_wait: float = 30.0  # 30s initial wait
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
        self.rate_limit_start = self._load_rate_limit_state()
        self._first_tweet = True
        logger.info(f"Initialized X client (wait_time={wait_time}s, initial_wait={initial_wait}s)")
    
    def _get_rate_limit_file(self) -> str:
        """Get path to rate limit state file."""
        return os.path.join(os.path.dirname(__file__), 'rate_limit_state.json')
    
    def _load_rate_limit_state(self) -> Optional[datetime]:
        """Load rate limit state from file."""
        try:
            file_path = self._get_rate_limit_file()
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('rate_limit_start'):
                        return datetime.fromisoformat(data['rate_limit_start'])
        except Exception as e:
            logger.error(f"Error loading rate limit state: {e}")
        return None
    
    def _save_rate_limit_state(self) -> None:
        """Save rate limit state to file."""
        try:
            file_path = self._get_rate_limit_file()
            data = {
                'rate_limit_start': self.rate_limit_start.isoformat() if self.rate_limit_start else None
            }
            with open(file_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving rate limit state: {e}")
    
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
    
    async def _check_rate_limit(self) -> None:
        """Check if we're currently rate limited and wait if necessary."""
        if self.rate_limit_start:
            elapsed = (datetime.now() - self.rate_limit_start).total_seconds()
            if elapsed < 900:  # 15 minutes
                wait_time = 900 - elapsed
                logger.warning(f"Still in rate limit window. Waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
            self.rate_limit_start = None
            self._save_rate_limit_state()
    
    async def _wait_for_rate_limit(self) -> None:
        """Ensure proper spacing between tweets."""
        # Handle initial wait for first tweet
        if self._first_tweet:
            logger.info(f"Initial wait of {self.initial_wait}s before first tweet...")
            await asyncio.sleep(self.initial_wait)
            self._first_tweet = False
            return

        # Normal tweet spacing
        now = datetime.now()
        if self.last_tweet_time:
            elapsed = (now - self.last_tweet_time).total_seconds()
            if elapsed < self.wait_time:
                wait_time = self.wait_time - elapsed
                logger.info(f"Waiting {wait_time:.1f}s before next tweet...")
                await asyncio.sleep(wait_time)
    
    async def create_tweet(
        self,
        text: str,
        reply_to: Optional[str] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Create a tweet with rate limiting and retries."""
        # Check if we're rate limited first
        await self._check_rate_limit()
        
        # Ensure proper spacing between tweets
        await self._wait_for_rate_limit()
        
        url = 'https://api.twitter.com/2/tweets'
        data = {"text": text}
        if reply_to:
            data["reply"] = {"in_reply_to_tweet_id": reply_to}
        
        try:
            headers = self._generate_auth_headers('POST', url)
            logger.info("Attempting to post tweet...")
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    status = response.status
                    
                    if status == 201 and 'data' in result:
                        logger.info("Successfully posted tweet")
                        self.last_tweet_time = datetime.now()  # Update only after successful tweet
                        return {
                            'success': True,
                            'id': str(result['data']['id']),
                            'text': text
                        }
                    elif status == 429:
                        self.rate_limit_start = datetime.now()
                        self._save_rate_limit_state()
                        wait_time = min(900 * (2 ** retry_count), 3600)  # Exponential backoff, max 1 hour
                        logger.warning(f"Rate limited. Waiting {wait_time/60:.1f} minutes...")
                        await asyncio.sleep(wait_time)
                        
                        if retry_count < self.max_retries:
                            logger.info("Retrying tweet after rate limit wait...")
                            return await self.create_tweet(text, reply_to, retry_count + 1)
                        else:
                            error_msg = "Max retries exceeded after rate limiting"
                            logger.error(error_msg)
                            return {
                                'success': False,
                                'error': error_msg,
                                'status': status
                            }
                    else:
                        error_msg = f"Error posting tweet: {result}"
                        logger.error(error_msg)
                        return {
                            'success': False,
                            'error': error_msg,
                            'status': status
                        }
                    
        except Exception as e:
            error_msg = f"Error creating tweet: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def create_thread(self, tweets: List[str]) -> List[Dict[str, Any]]:
        """Create a thread of tweets with rate limiting."""
        # Check rate limit state at start of thread
        await self._check_rate_limit()
        
        results = []
        reply_to = None
        
        logger.info(f"Starting thread of {len(tweets)} tweets with {self.wait_time}s spacing")
        
        for i, tweet in enumerate(tweets, 1):
            result = await self.create_tweet(tweet, reply_to)
            results.append(result)
            
            if result['success']:
                reply_to = result['id']
                logger.info(f"Posted tweet {i} of {len(tweets)}")
            else:
                logger.error(f"Failed to post tweet {i}. Stopping thread.")
                break
        
        logger.info("Thread complete")
        return results
    
    @classmethod
    def from_env(cls, wait_time: float = 60.0) -> 'XClient':
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