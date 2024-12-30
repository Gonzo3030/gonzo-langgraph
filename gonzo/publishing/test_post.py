"""Test endpoint for X API posting."""
import os
import ssl
import hmac
import time
import base64
import certifi
import logging
import asyncio
import urllib.parse
from typing import Dict
import aiohttp
import hashlib
import secrets

logger = logging.getLogger(__name__)

class SimpleXPoster:
    """Simple X API test poster using v2 endpoints."""
    
    def __init__(self, 
                 api_key: str,
                 api_secret: str,
                 access_token: str,
                 access_token_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
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
    
    async def test_post(self, message: str) -> Dict:
        """Test posting a single message to X."""
        url = 'https://api.twitter.com/2/tweets'
        data = {"text": message}
        
        headers = self._generate_auth_headers('POST', url)
        logger.info(f"Generated headers for test post")
        
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    status = response.status
                    
                    logger.info(f"Post attempt result - Status: {status}")
                    if result:
                        logger.info(f"Response data: {result}")
                        
                    return {
                        'success': status == 201,
                        'status': status,
                        'response': result
                    }
                    
        except Exception as e:
            error_msg = f"Error in test post: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    @classmethod
    async def test_credentials(cls) -> Dict:
        """Test X API credentials with a simple post."""
        try:
            required_vars = [
                'X_API_KEY',
                'X_API_SECRET',
                'X_ACCESS_TOKEN',
                'X_ACCESS_SECRET'
            ]
            
            # Check environment variables
            missing = [var for var in required_vars if not os.getenv(var)]
            if missing:
                return {
                    'success': False,
                    'error': f"Missing environment variables: {missing}"
                }
            
            # Create test instance
            poster = cls(
                api_key=os.getenv('X_API_KEY'),
                api_secret=os.getenv('X_API_SECRET'),
                access_token=os.getenv('X_ACCESS_TOKEN'),
                access_token_secret=os.getenv('X_ACCESS_SECRET')
            )
            
            # Try to post a test message
            test_message = "Test post from Gonzo AI - checking API functionality."
            result = await poster.test_post(test_message)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Test failed: {str(e)}"
            }