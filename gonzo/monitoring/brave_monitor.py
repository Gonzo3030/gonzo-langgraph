"""Brave API monitoring implementation."""
import os
import ssl
import certifi
import logging
import aiohttp
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, calls_per_second: int = 1):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0
    
    async def wait(self):
        """Wait if necessary to comply with rate limits."""
        current_time = datetime.now().timestamp()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < (1.0 / self.calls_per_second):
            wait_time = (1.0 / self.calls_per_second) - time_since_last_call
            await asyncio.sleep(wait_time)
        
        self.last_call_time = datetime.now().timestamp()

class BraveMonitor:
    """Handles Brave API searches for relevant content."""
    
    BASE_URL = "https://api.search.brave.com/res/v1/news/search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        # Create SSL context with certifi certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        # Initialize rate limiter
        self.rate_limiter = RateLimiter()
        logger.info(f"Initializing BraveMonitor with API key: {api_key[:8]}...")
    
    async def search_news(self, query: str, count: int = 10, max_retries: int = 3) -> List[Dict[str, Any]]:
        """Search for news articles using Brave API with retry logic."""
        params = {
            "q": query,
            "count": str(count),
            "freshness": "pd",  # Past day
            "text_format": "plain",
            "snippets": "1"
        }
        
        logger.info(f"Searching Brave API for: {query}")
        
        for attempt in range(max_retries):
            try:
                # Wait for rate limit
                await self.rate_limiter.wait()
                
                connector = aiohttp.TCPConnector(ssl=self.ssl_context)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(
                        self.BASE_URL,
                        headers=self.headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_text = await response.text()
                        
                        if response.status == 429:  # Rate limit exceeded
                            retry_after = int(response.headers.get('Retry-After', 2))
                            logger.warning(f"Rate limit hit, waiting {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        if response.status != 200:
                            logger.error(f"Brave API error ({response.status}): {response_text[:500]}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(1)  # Wait before retry
                                continue
                            raise Exception(f"Brave API error: {response.status}")
                        
                        data = await response.json()
                        logger.debug(f"API Response: {str(data)[:500]}...")
                        
                        # Extract results and handle possible missing fields
                        results = data.get("results", [])
                        news_items = [{
                            "title": item.get("title", ""),
                            "description": item.get("description", "") or item.get("snippet", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", "") or item.get("siteName", "")
                        } for item in results if item]
                        
                        logger.info(f"Found {len(news_items)} news items for query: {query}")
                        return news_items
                        
            except Exception as e:
                logger.error(f"Error in search_news (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    raise
    
    @staticmethod
    def generate_queries() -> List[str]:
        """Generate search queries focused on Russell Brand content."""
        queries = [
            # Direct Brand Content
            'Russell Brand latest news',
            'Russell Brand Rumble show',
            'Stay Free with Russell Brand',
            
            # Brand's Key Topics
            'Russell Brand big pharma',
            'Russell Brand corporate media',
            'Russell Brand censorship',
            'Russell Brand conspiracy',
            'Russell Brand controversy',
            
            # Brand's Commentary
            'Russell Brand political commentary',
            'Russell Brand system critique',
            'Russell Brand establishment',
            
            # Related Platforms/Channels
            'Russell Brand Rumble channel',
            'Russell Brand alternative media'
        ]
        logger.info(f"Generated {len(queries)} Russell Brand-focused queries")
        return queries