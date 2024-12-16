"""Social media monitoring implementation."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from textblob import TextBlob
from twitter.twitter_api_v2 import TwitterAPI

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
        self.client = TwitterAPI(
            api_key=api_key,
            api_secret=api_secret,
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
        metrics = tweet.get('public_metrics', {})
        return {
            "likes": metrics.get('like_count', 0),
            "retweets": metrics.get('retweet_count', 0),
            "replies": metrics.get('reply_count', 0),
            "quotes": metrics.get('quote_count', 0)
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
                response = self.client.search_tweets(
                    q=term,
                    tweet_fields=['created_at', 'public_metrics', 'author_id'],
                    max_results=100
                )
                
                if not response or 'data' not in response:
                    continue
                
                for tweet in response['data']:
                    if tweet['id'] in self.processed_ids:
                        continue
                        
                    engagement = self.calculate_engagement(tweet)
                    sentiment = self.calculate_sentiment(tweet['text'])
                    
                    if self.is_significant(engagement):
                        events.append(SocialEvent(
                            content=tweet['text'],
                            author=tweet['author_id'],
                            timestamp=datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                            platform="twitter",
                            engagement=engagement,
                            sentiment=sentiment,
                            metadata={
                                "tweet_id": tweet['id'],
                                "search_term": term
                            }
                        ))
                    
                    self.processed_ids.add(tweet['id'])
                    
            except Exception as e:
                print(f"Error searching {term}: {str(e)}")
                continue
                
        return events
    
    async def monitor_influencers(self) -> List[SocialEvent]:
        """Monitor key influencer activity."""
        events = []
        
        for username in self.influencers:
            try:
                # Get user's ID first
                user_response = self.client.get_user_by_username(username)
                if not user_response or 'data' not in user_response:
                    continue
                
                user_id = user_response['data']['id']
                
                # Get user's tweets
                tweets_response = self.client.get_user_tweets(
                    user_id,
                    tweet_fields=['created_at', 'public_metrics'],
                    max_results=20
                )
                
                if not tweets_response or 'data' not in tweets_response:
                    continue
                
                for tweet in tweets_response['data']:
                    if tweet['id'] in self.processed_ids:
                        continue
                    
                    engagement = self.calculate_engagement(tweet)
                    sentiment = self.calculate_sentiment(tweet['text'])
                    
                    events.append(SocialEvent(
                        content=tweet['text'],
                        author=username,
                        timestamp=datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                        platform="twitter",
                        engagement=engagement,
                        sentiment=sentiment,
                        metadata={
                            "tweet_id": tweet['id'],
                            "influencer": username
                        }
                    ))
                    
                    self.processed_ids.add(tweet['id'])
                    
            except Exception as e:
                print(f"Error monitoring {username}: {str(e)}")
                continue
                
        return events