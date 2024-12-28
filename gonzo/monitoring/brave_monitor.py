"""Brave API monitoring implementation."""
import os
import ssl
import certifi
import logging
import aiohttp
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BraveMonitor:
    """Handles Brave API searches for relevant content."""
    
    BASE_URL = "https://api.search.brave.com/app/search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        # Create SSL context with certifi certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        logger.info(f"Initializing BraveMonitor with API key: {api_key[:8]}...")
    
    async def search_news(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Search for news articles using Brave API."""
        params = {
            "q": query,
            "count": count,
            "search_type": "news",  # Specifically search for news
            "text_format": "plain",
            "freshness": "past_day",
            "safesearch": "moderate"
        }
        
        logger.info(f"Searching Brave API for: {query}")
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(
                    self.BASE_URL,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        logger.error(f"Brave API error: {response.status} - {response_text[:500]}")
                        raise Exception(f"Brave API error: {response.status}")
                    
                    data = await response.json()
                    articles = data.get("news", [])
                    logger.info(f"Found {len(articles)} articles for query: {query}")
                    return articles
                    
            except Exception as e:
                logger.error(f"Error in search_news: {str(e)}")
                raise
    
    @staticmethod
    def generate_queries() -> List[str]:
        """Generate search queries based on Gonzo's interests."""
        queries = [
            # Tech and AI developments
            'artificial intelligence regulation developments',
            'tech surveillance privacy',
            
            # Corporate/Political manipulation
            'corporate media manipulation',
            'big tech censorship',
            'political propaganda exposure',
            
            # Economic and Crypto
            'cryptocurrency regulation news',
            'central bank digital currency',
            'decentralized finance impact',
            
            # Health and Control
            'big pharma controversy',
            'medical freedom rights',
            
            # Alternative Media
            'Russell Brand news',  # Specific focus on Brand's content
            'alternative media censorship'
        ]
        logger.info(f"Generated {len(queries)} search queries")
        return queries