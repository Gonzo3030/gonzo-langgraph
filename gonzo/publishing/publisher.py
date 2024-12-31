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
        self.failed_posts_window = timedelta(hours=24)  # Only track failures for 24 hours
        self.failed_posts: Dict[str, datetime] = {}  # Track failed post hashes with timestamp
        logger.info("Initialized publisher")
    
    def _hash_thread(self, thread: List[str]) -> str:
        """Create a simple hash of thread content to track duplicates."""
        return '|'.join(thread)
    
    def _clean_failed_posts(self) -> None:
        """Remove old failed posts from tracking."""
        now = datetime.now()
        self.failed_posts = {
            hash_: timestamp
            for hash_, timestamp in self.failed_posts.items()
            if now - timestamp < self.failed_posts_window
        }
    
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
        
        # Clean old failed posts first
        self._clean_failed_posts()
        
        # Check if we've tried this thread recently
        thread_hash = self._hash_thread(thread)
        if thread_hash in self.failed_posts:
            fail_time = self.failed_posts[thread_hash]
            hours_ago = (datetime.now() - fail_time).total_seconds() / 3600
            logger.warning(f"Skipping thread that failed {hours_ago:.1f} hours ago")
            return {
                'success': False,
                'error': 'Recently failed thread'
            }
        
        try:
            # Wait appropriate time since last thread
            await self._wait_for_next_thread()
            
            logger.info(f"Publishing thread of {len(thread)} tweets")
            results = await self.x_client.create_thread(thread)
            
            # Update tracking based on result
            if any(r.get('success', False) for r in results):
                self.last_thread = datetime.now()
            else:
                # Only track if it's a duplicate content error
                error = next((r.get('error', '') for r in results if not r.get('success')), '')
                if 'duplicate content' in error.lower() or 'too many requests' in error.lower():
                    self.failed_posts[thread_hash] = datetime.now()
            
            return {
                'success': len(results) == len(thread),
                'tweets': results
            }
            
        except Exception as e:
            error_msg = f"Error publishing thread: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _filter_queue(self, posts: List[Dict]) -> List[Dict]:
        """Filter queue to remove old/invalid posts."""
        now = datetime.now()
        valid_posts = []
        
        for post in posts:
            try:
                scheduled_time = datetime.fromisoformat(post['scheduled_time'])
                # Keep posts scheduled within last 24 hours or in future
                if now - scheduled_time < timedelta(hours=24) or scheduled_time > now:
                    valid_posts.append(post)
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid post in queue: {str(e)}")
        
        return valid_posts
    
    async def publish_insights(self, insights: List[Dict]) -> List[Dict[str, Any]]:
        """Publish insights as threads."""
        if not insights:
            return []
        
        # Clean and sort insights
        filtered_insights = self._filter_queue(insights)
        if len(filtered_insights) < len(insights):
            logger.info(f"Filtered out {len(insights) - len(filtered_insights)} old/invalid posts")
        
        results = []
        for insight in filtered_insights:
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
    def from_env(cls, wait_time: float = 30.0) -> 'Publisher':
        """Create publisher from environment variables."""
        x_client = XClient.from_env(wait_time=wait_time)
        return cls(x_client=x_client)