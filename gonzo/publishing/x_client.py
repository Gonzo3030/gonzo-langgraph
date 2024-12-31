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
        self.base_wait_time = wait_time
        self.current_wait_time = wait_time
        self.last_request = datetime.min
        self._consecutive_failures = 0
        logger.info("Initialized X client")
    
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
    
    async def _wait_for_next_request(self) -> None:
        """Handle adaptive rate limiting."""
        now = datetime.now()
        time_since_last = (now - self.last_request).total_seconds()
        
        if time_since_last < self.current_wait_time:
            wait_time = self.current_wait_time - time_since_last
            logger.info(f"Waiting {wait_time:.1f} seconds before next request")
            await asyncio.sleep(wait_time)
        
        self.last_request = now
    
    def _handle_rate_limit(self, success: bool) -> None:
        """Adjust wait times based on success/failure."""
        if success:
            # On success, gradually reduce wait time
            self._consecutive_failures = 0
            self.current_wait_time = max(
                self.base_wait_time,
                self.current_wait_time * 0.8  # Reduce by 20%
            )
        else:
            # On failure, increase wait time exponentially
            self._consecutive_failures += 1
            self.current_wait_time = min(
                300,  # Max 5 minutes
                self.current_wait_time * (2 ** self._consecutive_failures)
            )
            logger.warning(f"Increased wait time to {self.current_wait_time:.1f} seconds")
    
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
            await self._wait_for_next_request()
            
            headers = self._generate_auth_headers('POST', url)
            logger.info(f"Generated headers for tweet")
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    status = response.status
                    
                    if status == 201 and 'data' in result:
                        logger.info("Successfully created tweet")
                        self._handle_rate_limit(True)
                        return {
                            'success': True,
                            'id': str(result['data']['id']),
                            'text': text
                        }
                    else:
                        error_msg = f"Error posting tweet: {result}"
                        logger.error(error_msg)
                        self._handle_rate_limit(False)
                        return {
                            'success': False,
                            'error': error_msg,
                            'status': status
                        }
                    
        except Exception as e:
            error_msg = f"Error creating tweet: {str(e)}"
            logger.error(error_msg)
            self._handle_rate_limit(False)
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
                    # Extra wait between thread tweets
                    await asyncio.sleep(self.current_wait_time * 2)
                else:
                    # Check if it's a rate limit error
                    if result.get('status') == 429:
                        # Wait longer and retry this tweet
                        await asyncio.sleep(self.current_wait_time * 4)
                        continue
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
        
        return results
    
    @classmethod
    def from_env(cls, wait_time: float = 1.0) -> 'XClient':
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