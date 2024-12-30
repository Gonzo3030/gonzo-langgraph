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
        logger.info("Initialized publisher")
    
    async def publish_thread(self, thread: List[str]) -> Dict[str, Any]:
        """Publish a thread to X."""
        if not thread:
            logger.warning("No tweets to post")
            return {
                'success': False,
                'error': 'No tweets provided'
            }
        
        try:
            logger.info(f"Publishing thread of {len(thread)} tweets")
            results = await self.x_client.create_thread(thread)
            
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
    
    def _schedule_insights(self, insights: List[Dict]) -> List[Dict]:
        """Schedule insights for publication."""
        now = datetime.now()
        scheduled_insights = []
        
        for i, insight in enumerate(insights):
            # First insight posts immediately, others scheduled hourly
            scheduled_time = now + timedelta(hours=i) if i > 0 else now
            
            scheduled_insights.append({
                'insight': insight,
                'scheduled_time': scheduled_time,
                'status': 'scheduled' if i > 0 else 'ready'
            })
            
            if i > 0:
                logger.info(f"Scheduled insight for {scheduled_time}")
            
        return scheduled_insights
    
    async def publish_insights(self, insights: List[Dict]) -> List[Dict[str, Any]]:
        """Publish first insight, schedule others."""
        if not insights:
            return []
            
        # Schedule insights
        scheduled = self._schedule_insights(insights)
        results = []
        
        # Publish first insight immediately
        first = scheduled[0]
        try:
            logger.info("Publishing immediate insight")
            thread = first['insight'].get('thread', [])
            if thread:
                result = await self.publish_thread(thread)
                results.append({
                    'insight': first['insight'],
                    'published': result,
                    'timestamp': datetime.now().isoformat(),
                    'scheduled_time': first['scheduled_time']
                })
        except Exception as e:
            logger.error(f"Error publishing immediate insight: {str(e)}")
        
        # Add scheduled insights to results
        for insight in scheduled[1:]:
            results.append({
                'insight': insight['insight'],
                'published': {'status': 'scheduled'},
                'timestamp': None,
                'scheduled_time': insight['scheduled_time']
            })
        
        # Log schedule
        logger.info(f"Published 1 insight immediately, scheduled {len(scheduled)-1} for later")
        for result in results:
            if result['scheduled_time'] > now:
                logger.info(f"Scheduled insight for {result['scheduled_time']}")
        
        return results
    
    @classmethod
    def from_env(cls, wait_time: float = 1.0) -> 'Publisher':
        """Create publisher from environment variables."""
        x_client = XClient.from_env(wait_time=wait_time)
        return cls(x_client=x_client)