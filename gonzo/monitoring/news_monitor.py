"""Crypto news monitoring implementation using Brave API."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..state_management import UnifiedState

class NewsArticle(BaseModel):
    """Structure for news articles."""
    title: str
    url: str
    published_date: datetime
    source: str
    description: str
    relevance_score: float = 0.0

class NewsEvent(BaseModel):
    """Structure for significant news events."""
    title: str
    url: str
    published_date: datetime
    source: str
    description: str
    relevance_score: float
    topics: List[str]
    sentiment: float
    related_assets: List[str] = []

class NewsMonitor:
    """Monitors crypto news using Brave API."""
    
    def __init__(self):
        self.last_check = None
        self.processed_urls = set()
        self.configure_topics()
    
    def configure_topics(self):
        """Configure monitoring topics and keywords."""
        self.primary_topics = [
            "crypto whale movements",
            "bitcoin manipulation",
            "crypto trading bots",
            "market manipulation crypto",
            "suspicious crypto transactions",
            "large bitcoin transfers"
        ]
        
        self.asset_keywords = [
            "bitcoin", "btc",
            "ethereum", "eth",
            "crypto", "cryptocurrency",
            "digital assets", "blockchain"
        ]
    
    async def fetch_news(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Fetch news using Brave API."""
        try:
            # Use the provided brave_web_search function
            from gonzo.external import brave_web_search
            
            # Add time context to query
            time_bounded_query = f"{query} when:7d"  # Last 7 days
            
            response = await brave_web_search({
                'query': time_bounded_query,
                'count': count
            })
            
            return response.get('web', {}).get('results', [])
            
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            return []
    
    def calculate_relevance(self, article: Dict[str, Any]) -> float:
        """Calculate relevance score for an article."""
        score = 0.0
        text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
        
        # Check for primary topics
        for topic in self.primary_topics:
            if any(word in text for word in topic.split()):
                score += 0.3
        
        # Check for asset mentions
        for asset in self.asset_keywords:
            if asset in text:
                score += 0.1
        
        # Boost recent articles
        if 'when:1d' in text:
            score += 0.2
        elif 'when:7d' in text:
            score += 0.1
        
        return min(score, 1.0)
    
    def extract_topics(self, text: str) -> List[str]:
        """Extract relevant topics from text."""
        topics = []
        for topic in self.primary_topics:
            if any(word in text.lower() for word in topic.split()):
                topics.append(topic)
        return topics
    
    def extract_assets(self, text: str) -> List[str]:
        """Extract mentioned assets from text."""
        assets = []
        for asset in self.asset_keywords:
            if asset in text.lower():
                assets.append(asset)
        return list(set(assets))
    
    async def update_news_state(self, state: UnifiedState) -> UnifiedState:
        """Update news monitoring data in the unified state."""
        try:
            all_articles = []
            
            # Fetch news for each primary topic
            for topic in self.primary_topics:
                articles = await self.fetch_news(topic)
                
                for article in articles:
                    url = article.get('url')
                    
                    # Skip if already processed
                    if url in self.processed_urls:
                        continue
                    
                    # Calculate relevance
                    relevance = self.calculate_relevance(article)
                    
                    if relevance > 0.4:  # Threshold for significance
                        text = article.get('title', '') + ' ' + article.get('description', '')
                        
                        # Create news event
                        event = NewsEvent(
                            title=article.get('title', ''),
                            url=url,
                            published_date=datetime.now(),  # You might want to parse this from the article
                            source=article.get('source', ''),
                            description=article.get('description', ''),
                            relevance_score=relevance,
                            topics=self.extract_topics(text),
                            sentiment=0.0,  # You might want to add sentiment analysis
                            related_assets=self.extract_assets(text)
                        )
                        
                        # Add to state
                        if not hasattr(state, 'news_events'):
                            state.news_events = []
                        state.news_events.append(event.dict())
                        
                        # Mark as significant for analysis
                        if relevance > 0.7:
                            state.narrative.pending_analyses = True
                    
                    self.processed_urls.add(url)
            
            self.last_check = datetime.now()
            
        except Exception as e:
            print(f"Error in news monitoring: {str(e)}")
            state.api_errors.append(f"News monitoring error: {str(e)}")
        
        return state