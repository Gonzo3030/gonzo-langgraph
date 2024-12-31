"""Publishing implementation for Gonzo MVP with scheduling."""
import os
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta

from .x_client import XClient

logger = logging.getLogger(__name__)

class Publisher:
    """Handles publishing insights to social media with scheduling."""
    
    def __init__(self, x_client: XClient):
        """Initialize publisher with X client."""
        self.x_client = x_client
        self.last_thread = datetime.min
        self.min_thread_interval = 7200  # 2 hours between threads
        self.failed_posts = set()  # Track failed post hashes to avoid duplicates
        logger.info("Initialized publisher")
    
    def _hash_thread(self, thread: List[str]) -> str:
        """Create a simple hash of thread content to track duplicates."""
        return '|'.join(thread)
    
    async def _wait_for_next_thread(self) -> None:
        """Wait appropriate time between threads."""
        now = datetime.now()
        time_since_last = (now - self.last_thread).total_seconds()
        
        if time_since_last < self.min_thread_interval:
            wait_time = self.min_thread_interval - time_since_last
            hours = int(wait_time // 3600)
            minutes = int((wait_time % 3600) // 60)
            logger.info(f"Waiting {hours} hours and {minutes} minutes before next thread")
            await asyncio.sleep(wait_time)
    
    async def publish_thread(self, thread: List[str]) -> Dict[str, Any]:
        """Publish a thread to X."""
        if not thread:
            logger.warning("No tweets to post")
            return {
                'success': False,
                'error': 'No tweets provided'
            }
        
        # Check if we've tried this thread before
        thread_hash = self._hash_thread(thread)
        if thread_hash in self.failed_posts:
            logger.warning("Skipping previously failed thread to avoid duplicate content")
            return {
                'success': False,
                'error': 'Duplicate content detected'
            }
        
        try:
            # Wait appropriate time since last thread
            await self._wait_for_next_thread()
            
            logger.info(f"Publishing thread of {len(thread)} tweets")
            results = await self.x_client.create_thread(thread)
            
            # Update last thread time if any tweet succeeded
            if any(r.get('success', False) for r in results):
                self.last_thread = datetime.now()
            else:
                # If it failed, add to failed posts to avoid retrying
                self.failed_posts.add(thread_hash)
            
            return {
                'success': len(results) == len(thread),
                'tweets': results
            }
            
        except Exception as e:
            error_msg = f"Error publishing thread: {str(e)}"
            logger.error(error_msg)
            # Add to failed posts if we got a duplicate content error
            if 'duplicate content' in str(e).lower():
                self.failed_posts.add(thread_hash)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def publish_insights(self, insights: List[Dict]) -> List[Dict[str, Any]]:
        """Publish insights as threads."""
        if not insights:
            return []
            
        results = []
        
        for insight in insights:
            try:
                thread = insight.get('thread', [])
                if thread:
                    result = await self.publish_thread(thread)
                    results.append({
                        'insight': insight,
                        'published': result,
                        'timestamp': datetime.now().isoformat(),
                        'scheduled_time': insight.get('scheduled_time')
                    })
                    
                    if not result.get('success'):
                        logger.warning(f"Failed to publish thread: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error publishing insight: {str(e)}")
        
        return results
    
    @classmethod
    def from_env(cls, wait_time: float = 1.0) -> 'Publisher':
        """Create publisher from environment variables."""
        x_client = XClient.from_env(wait_time=wait_time)
        return cls(x_client=x_client)