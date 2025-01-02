"""Brave API monitoring implementation with enhanced breaking news detection."""
import os
import ssl
import certifi
import logging
import aiohttp
import asyncio
from typing import List, Dict, Any, Tuple
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
    """Handles Brave API searches with enhanced breaking news detection."""
    
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
        # Track recent breaking news to avoid duplicates
        self.recent_breaking_news = []
        logger.info(f"Initializing BraveMonitor with API key: {api_key[:8]}...")
    
    async def search_news(
        self, 
        query: str, 
        count: int = 10, 
        freshness: str = "pd",  # past day
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for news articles using Brave API with retry logic."""
        params = {
            "q": query,
            "count": str(count),
            "freshness": freshness,
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
                            "source": item.get("source", "") or item.get("siteName", ""),
                            "age": item.get("age", ""),
                            "score": item.get("score", 0)
                        } for item in results if item]
                        
                        logger.info(f"Found {len(news_items)} news items for query: {query}")
                        return news_items
                        
            except Exception as e:
                logger.error(f"Error in search_news (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    raise
    
    async def get_breaking_news(self) -> List[Dict[str, Any]]:
        """Search for breaking news using multiple indicators."""
        breaking_queries = [
            'breaking news',
            'just happened',
            'developing story',
            'urgent news'
        ]
        
        all_news = []
        for query in breaking_queries:
            try:
                # Search last 12 hours with higher result count
                news_items = await self.search_news(
                    query=query,
                    count=20,
                    freshness="ph12"  # past 12 hours
                )
                all_news.extend(news_items)
            except Exception as e:
                logger.error(f"Error fetching breaking news for query '{query}': {str(e)}")
        
        # Filter and score breaking news
        breaking_news = []
        for item in all_news:
            # Skip if we've recently seen this story
            if item['url'] in self.recent_breaking_news:
                continue
                
            # Calculate breaking news score based on multiple factors
            score = 0
            title = item['title'].lower()
            desc = item['description'].lower()
            
            # Keywords indicating breaking news
            breaking_indicators = ['breaking', 'urgent', 'just in', 'developing']
            score += sum(2 for indicator in breaking_indicators 
                        if indicator in title or indicator in desc)
            
            # Recent timeframe
            if 'minutes ago' in item.get('age', '').lower():
                score += 3
            elif 'hour ago' in item.get('age', '').lower():
                score += 2
            
            # Add item if it meets breaking news threshold
            if score >= 2:
                item['breaking_score'] = score
                breaking_news.append(item)
                self.recent_breaking_news.append(item['url'])
                
        # Keep recent breaking news list manageable
        self.recent_breaking_news = self.recent_breaking_news[-100:]
        
        # Sort by breaking news score
        breaking_news.sort(key=lambda x: x.get('breaking_score', 0), reverse=True)
        return breaking_news[:5]  # Return top 5 breaking stories

    @staticmethod
    def generate_queries() -> List[str]:
        """Generate search queries based on Gonzo's interests."""
        queries = [
            # Breaking News
            'breaking news',
            
            # Tech and AI developments
            'artificial intelligence regulation developments',
            'tech surveillance privacy',
            'tech monopoly power',
            
            # Corporate/Political manipulation
            'corporate media manipulation',
            'big tech censorship',
            'lobbying & legal corruption',
            'political propaganda exposure',
            'corporate corruption scandal',
            'Deep state establishment',
            
            # Economic and Crypto
            'cryptocurrency regulation news',
            'pump and dump schemes',
            'meme coin frenzy',
            'ai16Z eliza',
            'terminal of truths',
            'DeFi protocols',
            'central bank digital currency',
            'decentralized finance impact',
            'wall street manipulation',
            
            # Health and Control
            'big pharma controversy',
            'medical freedom rights',
            'healthcare system abuse',
            
            # Alternative Media and Free Speech
            'alternative media censorship',
            'X platform as a beacon of free speech',
            'independent journalism suppression',
            'whistleblower revelation',
            
            # Environmental 
            'climate crisis corporate',
            'environmental destruction profit'
        ]
        logger.info(f"Generated {len(queries)} search queries")
        return queries
