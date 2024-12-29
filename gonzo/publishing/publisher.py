"""Publishing implementation for Gonzo MVP."""
import os
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from .x_client import XClient

logger = logging.getLogger(__name__)

class Publisher:
    """Handles publishing insights to social media."""
    
    def __init__(self, x_client: XClient):
        """Initialize publisher with X client."""
        self.x_client = x_client
        logger.info("Initialized publisher")
    
    async def publish_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """Publish a thread to X.
        
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
        
        try:
            logger.info(f"Publishing thread of {len(tweets)} tweets")
            results = await self.x_client.create_thread(tweets)
            
            return {
                'success': True,
                'tweets': results
            }
            
        except Exception as e:
            error_msg = f"Error publishing thread: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def publish_insights(self, insights: List[Dict]) -> List[Dict[str, Any]]:
        """Publish all insight threads.
        
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
                    result = await self.publish_thread(thread)
                    results.append({
                        'insight': insight,
                        'published': result,
                        'timestamp': datetime.now().isoformat()
                    })
                    # Wait between threads
                    await asyncio.sleep(self.x_client.wait_time * 2)
                    
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
    def from_env(cls, wait_time: float = 1.0) -> 'Publisher':
        """Create publisher from environment variables."""
        x_client = XClient.from_env(wait_time=wait_time)
        return cls(x_client=x_client)