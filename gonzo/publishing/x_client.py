"""X (Twitter) API client implementation."""
import os
import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from tweepy import Client, Response

logger = logging.getLogger(__name__)

class XClient:
    """Wrapper for X API interactions with rate limiting."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        wait_time: float = 1.0
    ):
        self.client = Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        self.wait_time = wait_time
        self.last_request = datetime.min
        self._requests_remaining = 50  # X API default rate limit
        self._reset_time = datetime.now() + timedelta(minutes=15)
        
        logger.info("Initialized X client")
    
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
        try:
            await self._wait_for_rate_limit()
            
            response = self.client.create_tweet(
                text=text,
                in_reply_to_tweet_id=reply_to
            )
            
            if isinstance(response, Response):
                data = response.data
                logger.info("Successfully created tweet")
                return {
                    'success': True,
                    'id': str(data['id']),
                    'text': text
                }
            else:
                raise ValueError(f"Unexpected response type: {type(response)}")
                
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
    def from_env(
        cls,
        wait_time: float = 1.0
    ) -> 'XClient':
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
            access_secret=os.getenv('X_ACCESS_SECRET'),
            wait_time=wait_time
        )