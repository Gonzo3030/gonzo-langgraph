"""Twitter publishing implementation for Gonzo MVP."""
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import tweepy

logger = logging.getLogger(__name__)

class TwitterPublisher:
    """Handles publishing insights to Twitter."""
    
    def __init__(self, 
                 api_key: str,
                 api_secret: str, 
                 access_token: str, 
                 access_token_secret: str,
                 wait_time: float = 1.0):
        """Initialize Twitter API client.
        
        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Twitter access token
            access_token_secret: Twitter access token secret
            wait_time: Time to wait between tweets in seconds
        """
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        self.wait_time = wait_time
        logger.info("Initialized Twitter publisher")
        
    async def _create_thread(self, 
                            first_tweet: str, 
                            replies: List[str],
                            max_retries: int = 3) -> Dict[str, Any]:
        """Create a thread from first tweet and replies.
        
        Args:
            first_tweet: Content of the first tweet
            replies: List of reply tweet contents
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict containing thread info and status
        """
        result = {
            'success': False,
            'tweets': [],
            'error': None
        }
        
        try:
            # Post first tweet
            for attempt in range(max_retries):
                try:
                    response = self.client.create_tweet(text=first_tweet)
                    first_tweet_id = response.data['id']
                    result['tweets'].append({
                        'id': first_tweet_id,
                        'text': first_tweet,
                        'url': f"https://twitter.com/user/status/{first_tweet_id}"
                    })
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            # Post replies
            previous_id = first_tweet_id
            for reply in replies:
                await asyncio.sleep(self.wait_time)  # Rate limiting
                
                for attempt in range(max_retries):
                    try:
                        response = self.client.create_tweet(
                            text=reply,
                            in_reply_to_tweet_id=previous_id
                        )
                        tweet_id = response.data['id']
                        result['tweets'].append({
                            'id': tweet_id,
                            'text': reply,
                            'url': f"https://twitter.com/user/status/{tweet_id}"
                        })
                        previous_id = tweet_id
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            result['success'] = True
            logger.info(f"Successfully posted thread of {len(result['tweets'])} tweets")
            
        except Exception as e:
            error_msg = f"Error creating thread: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            
        return result
    
    async def post_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """Post a series of tweets as a thread.
        
        Args:
            tweets: List of tweet contents
            
        Returns:
            Dict containing thread info and status
        """
        if not tweets:
            logger.warning("No tweets to post")
            return {
                'success': False,
                'error': 'No tweets provided'
            }
            
        logger.info(f"Posting thread of {len(tweets)} tweets")
        return await self._create_thread(tweets[0], tweets[1:])
    
    async def publish_insights(self, insights: List[Dict]) -> List[Dict[str, Any]]:
        """Publish all insight threads to Twitter.
        
        Args:
            insights: List of insight dicts containing threads
            
        Returns:
            List of publishing results
        """
        results = []
        
        for insight in insights:
            try:
                thread = insight.get('thread', [])
                if thread:
                    logger.info(f"Publishing thread for insight")
                    result = await self.post_thread(thread)
                    results.append({
                        'insight': insight,
                        'published': result,
                        'timestamp': datetime.now().isoformat()
                    })
                    # Wait between threads
                    await asyncio.sleep(self.wait_time * 2)
                    
            except Exception as e:
                logger.error(f"Error publishing insight: {str(e)}")
                results.append({
                    'insight': insight,
                    'published': {
                        'success': False,
                        'error': str(e)
                    },
                    'timestamp': datetime.now().isoformat()
                })
        
        logger.info(f"Published {len(results)} insight threads")
        return results
    
    @classmethod
    def from_env(cls, wait_time: float = 1.0) -> 'TwitterPublisher':
        """Create TwitterPublisher from environment variables."""
        required_vars = [
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET',
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
            
        return cls(
            api_key=os.getenv('TWITTER_API_KEY'),
            api_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            wait_time=wait_time
        )