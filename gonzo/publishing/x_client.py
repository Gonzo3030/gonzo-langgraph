"""X (Twitter) API client implementation with enhanced debugging."""
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
    
    API_BASE_URL = "https://api.x.com/2"  # Updated URL
    
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
        self.rate_limit_start = None
        self._first_tweet = True
        logger.info(f"Initialized X client (wait_time={wait_time}s, initial_wait={initial_wait}s)")
    
    def _generate_auth_headers(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, str]:
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
        
        # Add data parameters to signature if present
        if data:
            flat_data = self._flatten_params(data)
            params.update(flat_data)
        
        # Sort parameters and create signature base string
        param_string = '&'.join([
            f"{urllib.parse.quote(key, safe='')}={urllib.parse.quote(str(value), safe='')}"
            for key, value in sorted(params.items())
        ])
        
        signature_base = '&'.join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_string, safe='')
        ])
        
        # Create signing key and generate signature
        signing_key = f"{urllib.parse.quote(self.api_secret, safe='')}&{urllib.parse.quote(self.access_token_secret, safe='')}"
        
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode('utf-8'),
                signature_base.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        # Only include OAuth params in header
        oauth_params = {k: v for k, v in params.items() if k.startswith('oauth_')}
        oauth_params['oauth_signature'] = signature
        
        auth_header = 'OAuth ' + ', '.join([
            f'{urllib.parse.quote(key, safe="")}="{urllib.parse.quote(str(value), safe="")}"'
            for key, value in sorted(oauth_params.items())
        ])
        
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        
        # Debug log the auth process
        logger.debug(f"URL: {url}")
        logger.debug(f"Method: {method}")
        logger.debug(f"Signature Base: {signature_base}")
        logger.debug(f"Auth Header: {auth_header}")
        
        return headers
    
    def _flatten_params(self, data: Dict, prefix: str = '') -> Dict[str, str]:
        """Flatten nested dictionary for OAuth 1.0a signing."""
        params = {}
        for key, value in data.items():
            if isinstance(value, dict):
                params.update(self._flatten_params(value, f"{prefix}{key}_"))
            else:
                params[f"{prefix}{key}"] = str(value)
        return params
    
    async def _handle_rate_limit(self, response: aiohttp.ClientResponse, retry_count: int = 0) -> bool:
        """Handle rate limiting with exponential backoff."""
        self.rate_limit_start = datetime.now()
        
        # Log rate limit headers
        headers = dict(response.headers)
        logger.warning("Rate limit headers:")
        for key, value in headers.items():
            if 'rate' in key.lower() or 'limit' in key.lower():
                logger.warning(f"{key}: {value}")
        
        # Get wait time from headers or use default
        wait_time = int(headers.get('x-rate-limit-reset', 900))
        wait_time = min(wait_time * (2 ** retry_count), 3600)  # Exponential backoff, max 1 hour
        
        logger.warning(f"Rate limited. Waiting {wait_time/60:.1f} minutes...")
        await asyncio.sleep(wait_time)
        return retry_count < self.max_retries
    
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
    
    async def create_tweet(
        self,
        text: str,
        reply_to: Optional[str] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Create a tweet with rate limiting and retries."""
        try:
            await self._wait_for_rate_limit()
            
            url = f"{self.API_BASE_URL}/tweets"
            data = {"text": text}
            if reply_to:
                data["reply"] = {"in_reply_to_tweet_id": reply_to}
            
            headers = self._generate_auth_headers('POST', url, data)
            logger.info("Attempting to post tweet...")
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    status = response.status
                    result = await response.json()
                    
                    # Log complete response for debugging
                    logger.debug(f"Response status: {status}")
                    logger.debug(f"Response headers: {dict(response.headers)}")
                    logger.debug(f"Response body: {result}")
                    
                    if status == 201 and 'data' in result:
                        logger.info("Successfully posted tweet")
                        self.last_tweet_time = datetime.now()
                        return {
                            'success': True,
                            'id': str(result['data']['id']),
                            'text': text
                        }
                    elif status == 429:  # Rate limit
                        if await self._handle_rate_limit(response, retry_count):
                            logger.info("Retrying tweet after rate limit wait...")
                            return await self.create_tweet(text, reply_to, retry_count + 1)
                        else:
                            error_msg = "Max retries exceeded after rate limiting"
                            logger.error(error_msg)
                            return {
                                'success': False,
                                'error': error_msg,
                                'status': status,
                                'details': result
                            }
                    else:
                        error_msg = f"Error posting tweet: {result}"
                        logger.error(error_msg)
                        return {
                            'success': False,
                            'error': error_msg,
                            'status': status,
                            'details': result
                        }
                    
        except Exception as e:
            error_msg = f"Error creating tweet: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def test_auth(self) -> Dict[str, Any]:
        """Test authentication by getting account information."""
        try:
            url = f"{self.API_BASE_URL}/users/me"
            headers = self._generate_auth_headers('GET', url)
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers) as response:
                    result = await response.json()
                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'details': result
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
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
