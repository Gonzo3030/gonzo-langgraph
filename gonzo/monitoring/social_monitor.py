"""Social media monitoring implementation."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from textblob import TextBlob

from .x_client import XClient, Tweet
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
        # Initialize X client
        self.client = XClient(
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token,
            access_secret=access_secret
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
            "VitalikButerin"
        ]
    
    def calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score for text."""
        analysis = TextBlob(text)
        return analysis.sentiment.polarity
    
    def calculate_engagement(self, tweet: Tweet) -> Dict[str, int]:
        """Calculate engagement metrics for a tweet."""
        return {
            "likes": tweet.public_metrics.get('like_count', 0),
            "retweets": tweet.public_metrics.get('retweet_count', 0),
            "replies": tweet.public_metrics.get('reply_count', 0),
            "quotes": tweet.public_metrics.get('quote_count', 0)
        }
    
    def is_significant(self, engagement: Dict[str, int], is_influencer: bool = False) -> bool:
        """Determine if engagement levels are significant."""
        if is_influencer:  # All influencer posts are significant
            return True
            
        total_engagement = sum(engagement.values())
        return total_engagement > 100  # Adjustable threshold
    
    async def monitor_social_activity(self) -> List[SocialEvent]:
        """Monitor all social activity."""
        events = []
        
        try:
            # Search discussions
            for term in self.search_terms:
                tweets = self.client.search_recent(term, max_results=100)
                
                for tweet in tweets:
                    if tweet.id in self.processed_ids:
                        continue
                        
                    engagement = self.calculate_engagement(tweet)
                    sentiment = self.calculate_sentiment(tweet.text)
                    
                    if self.is_significant(engagement):
                        events.append(SocialEvent(
                            content=tweet.text,
                            author=tweet.author_id,
                            timestamp=tweet.created_at,
                            platform="twitter",
                            engagement=engagement,
                            sentiment=sentiment,
                            metadata={
                                "tweet_id": tweet.id,
                                "search_term": term
                            }
                        ))
                        
                    self.processed_ids.add(tweet.id)
            
            # Monitor influencers
            for username in self.influencers:
                user = self.client.get_user_by_username(username)
                if not user:
                    continue
                    
                tweets = self.client.get_user_tweets(user['id'], max_results=20)
                
                for tweet in tweets:
                    if tweet.id in self.processed_ids:
                        continue
                        
                    engagement = self.calculate_engagement(tweet)
                    sentiment = self.calculate_sentiment(tweet.text)
                    
                    events.append(SocialEvent(
                        content=tweet.text,
                        author=username,
                        timestamp=tweet.created_at,
                        platform="twitter",
                        engagement=engagement,
                        sentiment=sentiment,
                        metadata={
                            "tweet_id": tweet.id,
                            "influencer": username
                        }
                    ))
                    
                    self.processed_ids.add(tweet.id)
            
        except Exception as e:
            print(f"Error in social monitoring: {str(e)}")
        
        return events