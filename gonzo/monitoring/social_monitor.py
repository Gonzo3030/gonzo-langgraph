"""Social media monitoring implementation."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import tweepy
from textblob import TextBlob

from .real_time_monitor import SocialEvent

class SocialMediaMonitor:
    """Monitors social media (primarily X) for relevant discussions."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str
    ):
        # Initialize X API client
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_secret)
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # Initialize tracking
        self.processed_ids = set()
        
        # Configure monitoring targets
        self.configure_targets()
    
    def configure_targets(self):
        """Configure monitoring targets and keywords"""
        self.search_terms = [
            "crypto manipulation",
            "market fraud",
            "whale alert",
            "crypto regulation",
            "defi hack",
            "crypto scam"
        ]
        
        self.influencers = [
            "whale_alert",
            "cz_binance",
            "VitalikButerin",
            "SBF_FTX"  # For historical context
        ]
    
    def calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score for text."""
        analysis = TextBlob(text)
        return analysis.sentiment.polarity
    
    def calculate_engagement(self, tweet: Any) -> Dict[str, int]:
        """Calculate engagement metrics for a tweet."""
        metrics = getattr(tweet, 'public_metrics', {})
        return {
            "likes": getattr(metrics, 'like_count', 0),
            "retweets": getattr(metrics, 'retweet_count', 0),
            "replies": getattr(metrics, 'reply_count', 0),
            "quotes": getattr(metrics, 'quote_count', 0)
        }
    
    def is_significant(self, engagement: Dict[str, int], is_influencer: bool = False) -> bool:
        """Determine if engagement levels are significant."""
        if is_influencer:  # All influencer posts are significant
            return True
            
        total_engagement = sum(engagement.values())
        return total_engagement > 100  # Adjustable threshold
    
    async def create_social_event(self, tweet: Any, source: str = "search") -> SocialEvent:
        """Create a social event from a tweet."""
        engagement = self.calculate_engagement(tweet)
        sentiment = self.calculate_sentiment(tweet.text)
        
        return SocialEvent(
            content=tweet.text,
            author=str(tweet.author_id),
            timestamp=tweet.created_at,
            platform="twitter",
            engagement=engagement,
            sentiment=sentiment,
            metadata={
                "tweet_id": str(tweet.id),
                "source": source
            }
        )
    
    async def monitor_social_activity(self) -> List[SocialEvent]:
        """Monitor all social activity."""
        events = []
        
        try:
            # Search discussions
            search_events = await self.search_discussions()
            events.extend(search_events)
            
            # Monitor influencers
            influencer_events = await self.monitor_influencers()
            events.extend(influencer_events)
            
        except Exception as e:
            print(f"Error in social monitoring: {str(e)}")
        
        return events
    
    async def search_discussions(self) -> List[SocialEvent]:
        """Search for relevant discussions."""
        events = []
        
        for term in self.search_terms:
            try:
                tweets = self.client.search_recent_tweets(
                    query=term,
                    tweet_fields=["created_at", "public_metrics", "author_id"],
                    max_results=100
                )
                
                if not tweets.data:
                    continue
                
                for tweet in tweets.data:
                    if tweet.id in self.processed_ids:
                        continue
                        
                    event = await self.create_social_event(tweet, f"search:{term}")
                    if self.is_significant(event.engagement):
                        events.append(event)
                    
                    self.processed_ids.add(tweet.id)
                    
            except Exception as e:
                print(f"Error searching {term}: {str(e)}")
                continue
                
        return events
    
    async def monitor_influencers(self) -> List[SocialEvent]:
        """Monitor key influencer activity."""
        events = []
        
        for username in self.influencers:
            try:
                user = self.client.get_user(username=username)
                if not user.data:
                    continue
                
                tweets = self.client.get_users_tweets(
                    user.data.id,
                    tweet_fields=["created_at", "public_metrics"],
                    max_results=20
                )
                
                if not tweets.data:
                    continue
                
                for tweet in tweets.data:
                    if tweet.id in self.processed_ids:
                        continue
                        
                    event = await self.create_social_event(
                        tweet,
                        f"influencer:{username}"
                    )
                    events.append(event)  # All influencer tweets are significant
                    
                    self.processed_ids.add(tweet.id)
                    
            except Exception as e:
                print(f"Error monitoring {username}: {str(e)}")
                continue
                
        return events