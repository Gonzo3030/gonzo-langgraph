"""Brave API monitoring implementation."""
import os
import aiohttp
from typing import List, Dict, Any
from datetime import datetime, timedelta

class BraveMonitor:
    """Handles Brave API searches for relevant content."""
    
    BASE_URL = "https://api.search.brave.com/news/search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
    
    async def search_news(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Search for news articles using Brave API."""
        params = {
            "q": query,
            "count": count,
            "freshness": "p1d"  # Past day
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.BASE_URL,
                headers=self.headers,
                params=params
            ) as response:
                if response.status != 200:
                    raise Exception(f"Brave API error: {response.status}")
                
                data = await response.json()
                return data.get("articles", [])
    
    @staticmethod
    def generate_queries() -> List[str]:
        """Generate search queries based on Gonzo's interests."""
        return [
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
