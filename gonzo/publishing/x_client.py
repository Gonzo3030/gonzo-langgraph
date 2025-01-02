"""X (Twitter) API client implementation with fixed authentication."""
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
    
    API_BASE_URL = "https://api.twitter.com/2"  # Fixed URL
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        wait_time: float = 3.0,
        max_retries: int = 3,
        initial_wait: float = 5.0
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
        """Generate OAuth 1.0a headers for X API v2."""
        oauth_timestamp = str(int(time.time()))
        oauth_nonce = secrets.token_hex(32)
        
        # Core OAuth parameters
        oauth_params = {
            'oauth_consumer_key': self.api_key,
            'oauth_nonce': oauth_nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': oauth_timestamp,
            'oauth_token': self.access_token,
            'oauth_version': '1.0'
        }
        
        # For POST requests, add data to params for signature
        params = oauth_params.copy()
        if method.upper() == 'POST' and data:
            params.update(self._flatten_params(data))
        
        # Create parameter string
        param_string = '&'.join(
            f"{urllib.parse.quote(str(k), safe='')}={urllib.parse.quote(str(v), safe='')}"
            for k, v in sorted(params.items())
        )
        
        # Create signature base string
        signature_base = '&'.join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_string, safe='')
        ])
        
        # Create signing key
        signing_key = (
            urllib.parse.quote(self.api_secret, safe='') + 
            '&' + 
            urllib.parse.quote(self.access_token_secret, safe='')
        )
        
        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode('utf-8'),
                signature_base.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        # Add signature to OAuth parameters
        oauth_params['oauth_signature'] = signature
        
        # Create Authorization header
        auth_header = 'OAuth ' + ', '.join(
            f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(str(v), safe="")}"'
            for k, v in sorted(oauth_params.items())
        )
        
        # Log debug info
        logger.debug(f"URL: {url}")
        logger.debug(f"Method: {method}")
        logger.debug(f"Base string: {signature_base}")
        logger.debug(f"Signature: {signature}")
        logger.debug(f"Auth header: {auth_header}")
        
        return {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
    
    def _flatten_params(self, data: Dict, prefix: str = '') -> Dict[str, str]:
        """Flatten nested dictionary for OAuth 1.0a signing."""
        params = {}
        for key, value in data.items():
            if isinstance(value, dict):
                params.update(self._flatten_params(value, f"{prefix}{key}."))
            elif isinstance(value, (list, tuple)):
                for i, item in enumerate(value):
                    params.update(self._flatten_params({str(i): item}, f"{prefix}{key}."))
            else:
                params[f"{prefix}{key}"] = str(value)
        return params

    async def test_auth(self) -> Dict[str, Any]:
        """Test authentication by getting account information."""
        try:
            url = f"{self.API_BASE_URL}/users/me"
            headers = self._generate_auth_headers('GET', url)
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    result = await response.json()
                    
                    logger.debug(f"Auth test response status: {status}")
                    logger.debug(f"Auth test response headers: {dict(response.headers)}")
                    logger.debug(f"Auth test response body: {result}")
                    
                    return {
                        'success': status == 200,
                        'status': status,
                        'details': result
                    }
        except Exception as e:
            logger.error(f"Auth test error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ... rest of the class implementation remains the same ...
