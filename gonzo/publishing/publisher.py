"""Enhanced publishing implementation with better error handling and state management."""
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

from .x_client import XClient

logger = logging.getLogger(__name__)

class Publisher:
    """Handles publishing insights to social media with enhanced error handling."""
    
    def __init__(self, x_client: XClient):
        """Initialize publisher with X client."""
        self.x_client = x_client
        self.last_thread = datetime.min
        self.min_thread_interval = 7200  # 2 hours between threads
        self.retry_window = timedelta(hours=1)  # Only retry within this window
        self.failed_posts: Dict[str, Dict[str, Any]] = {}  # Track failed posts with details
        self._current_task = None
        logger.info("Initialized publisher")
    
    def _hash_thread(self, thread: List[str]) -> str:
        """Create a robust hash of thread content."""
        # Normalize and concatenate tweets
        thread_text = '|'.join(tweet.strip().lower() for tweet in thread)
        # Create SHA-256 hash
        return hashlib.sha256(thread_text.encode()).hexdigest()
    
    def _clean_failed_posts(self) -> None:
        """Remove expired failed posts from tracking."""
        now = datetime.now()
        self.failed_posts = {
            hash_: data
            for hash_, data in self.failed_posts.items()
            if now - data['timestamp'] < self.retry_window
        }
    
    def _is_retryable_error(self, error: str) -> bool:
        """Determine if an error should allow retries."""
        non_retryable = [
            'duplicate content',
            'not permitted',
            'forbidden',
            'invalid authentication',
            'authorization'
        ]
        error_lower = error.lower()
        return not any(msg in error_lower for msg in non_retryable)
    
    async def _wait_for_next_thread(self) -> None:
        """Ensure proper spacing between threads."""
        now = datetime.now()
        time_since_last = (now - self.last_thread).total_seconds()
        
        if time_since_last < self.min_thread_interval:
            wait_time = self.min_thread_interval - time_since_last
            hours = int(wait_time // 3600)
            minutes = int((wait_time % 3600) // 60)
            logger.info(f"Waiting {hours} hours and {minutes} minutes before next thread")
            await asyncio.sleep(wait_time)
    
    async def publish_thread(self, thread: List[str]) -> Dict[str, Any]:
        """Publish a thread with enhanced error handling and state management."""
        if not thread:
            logger.warning("No tweets to post")
            return {
                'success': False,
                'error': 'No tweets provided'
            }
        
        # Clean old failed posts first
        self._clean_failed_posts()
        
        # Check thread history
        thread_hash = self._hash_thread(thread)
        if thread_hash in self.failed_posts:
            fail_data = self.failed_posts[thread_hash]
            error = fail_data['error']
            hours_ago = (datetime.now() - fail_data['timestamp']).total_seconds() / 3600
            
            # If error is retryable and within window, allow retry
            if not self._is_retryable_error(error):
                logger.warning(f"Skipping thread that failed with '{error}' {hours_ago:.1f} hours ago")
                return {
                    'success': False,
                    'error': 'Previous non-retryable error: ' + error
                }
            elif hours_ago < 1:  # Wait at least an hour between retries
                logger.warning(f"Too soon to retry thread (failed {hours_ago:.1f} hours ago)")
                return {
                    'success': False,
                    'error': 'Too soon to retry'
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
                    self.x_client.create_tweet(tweet, reply_to)
                )
                
                try:
                    result = await self._current_task
                    results.append(result)
                    
                    if result['success']:
                        reply_to = result['id']
                        logger.info(f"Posted tweet {i} of {len(thread)}")
                    else:
                        error = result.get('error', 'Unknown error')
                        logger.error(f"Failed to post tweet {i}: {error}")
                        
                        # Track failure with details
                        self.failed_posts[thread_hash] = {
                            'timestamp': datetime.now(),
                            'error': error,
                            'attempt': i,
                            'retryable': self._is_retryable_error(error)
                        }
                        break
                        
                except asyncio.CancelledError:
                    logger.info("Thread publishing cancelled")
                    raise
                finally:
                    self._current_task = None
            
            # Update last thread time only on complete success
            if all(r.get('success', False) for r in results):
                self.last_thread = datetime.now()
                # Clear any failed post record on success
                self.failed_posts.pop(thread_hash, None)
            
            return {
                'success': len(results) == len(thread) and all(r.get('success', False) for r in results),
                'tweets': results,
                'completed': len(results)
            }
            
        except asyncio.CancelledError:
            logger.info("Thread publishing process cancelled")
            raise
        except Exception as e:
            error_msg = f"Error publishing thread: {str(e)}"
            logger.error(error_msg)
            # Track unexpected errors
            self.failed_posts[thread_hash] = {
                'timestamp': datetime.now(),
                'error': error_msg,
                'attempt': 0,
                'retryable': True  # Allow retry for unexpected errors
            }
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
    def from_env(cls, wait_time: float = 3.0) -> 'Publisher':
        """Create publisher from environment variables."""
        x_client = XClient.from_env(wait_time=wait_time)
        return cls(x_client=x_client)
