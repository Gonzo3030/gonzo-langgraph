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
        self._current_task = None  # Track current publishing task
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

    async def _publish_single_tweet(self, tweet: str, reply_to: str = None) -> Dict[str, Any]:
        """Publish a single tweet with proper error handling."""
        try:
            result = await self.x_client.create_tweet(tweet, reply_to)
            return result
        except asyncio.CancelledError:
            logger.info("Tweet publishing cancelled")
            raise
        except Exception as e:
            logger.error(f"Error publishing tweet: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
            
            results = []
            reply_to = None
            
            for i, tweet in enumerate(thread, 1):
                # Create and track the task
                self._current_task = asyncio.create_task(
                    self._publish_single_tweet(tweet, reply_to)
                )
                
                try:
                    result = await self._current_task
                    results.append(result)
                    
                    if result['success']:
                        reply_to = result['id']
                        logger.info(f"Posted tweet {i} of {len(thread)}")
                    else:
                        logger.error(f"Failed to post tweet {i}. Stopping thread.")
                        break
                        
                except asyncio.CancelledError:
                    logger.info("Thread publishing cancelled")
                    raise
                finally:
                    self._current_task = None
            
            # Update tracking based on results
            if any(r.get('success', False) for r in results):
                self.last_thread = datetime.now()
            else:
                # Only track if it's a duplicate content error or rate limit
                error = next((r.get('error', '') for r in results if not r.get('success')), '')
                if 'duplicate content' in error.lower() or 'too many requests' in error.lower():
                    self.failed_posts[thread_hash] = datetime.now()
            
            return {
                'success': len(results) == len(thread),
                'tweets': results
            }
            
        except asyncio.CancelledError:
            logger.info("Thread publishing process cancelled")
            raise
        except Exception as e:
            error_msg = f"Error publishing thread: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        
    async def cancel_current_task(self):
        """Cancel the current publishing task if any."""
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
    
    @classmethod
    def from_env(cls, wait_time: float = 60.0) -> 'Publisher':
        """Create publisher from environment variables."""
        x_client = XClient.from_env(wait_time=wait_time)
        return cls(x_client=x_client)