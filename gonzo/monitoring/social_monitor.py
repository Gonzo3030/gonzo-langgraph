"""Social media monitoring implementation."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from textblob import TextBlob

from ..state_management import UnifiedState, SocialData
from .x_client import XClient, Tweet, RateLimitError
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
    
    async def update_social_state(self, state: UnifiedState) -> UnifiedState:
        """Update social monitoring data in the unified state."""
        try:
            # Check if we should throttle based on rate limits
            if state.x_integration.rate_limits["remaining"] <= 1:
                if state.x_integration.rate_limits["reset_time"] > datetime.now():
                    print("Rate limit reached, skipping social monitoring cycle")
                    return state
            
            # Search discussions
            for term in self.search_terms:
                try:
                    tweets, remaining, reset_time = await self.client.search_recent(term, max_results=100)
                    
                    # Update rate limits in state
                    state.x_integration.rate_limits.update({
                        "remaining": remaining,
                        "reset_time": reset_time,
                        "last_request": datetime.now()
                    })
                    
                    for tweet in tweets:
                        if tweet.id in self.processed_ids:
                            continue
                            
                        engagement = self.calculate_engagement(tweet)
                        sentiment = self.calculate_sentiment(tweet.text)
                        
                        if self.is_significant(engagement):
                            # Create social data instance
                            social_data = SocialData(
                                content=tweet.text,
                                timestamp=tweet.created_at,
                                metrics=engagement,
                                author_id=tweet.author_id
                            )
                            
                            # Add to state
                            state.social_data.append(social_data)
                            
                            # If significant, add as event
                            event = SocialEvent(
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
                            )
                            state.narrative.social_events.append(event.__dict__)
                            state.narrative.pending_analyses = True
                            
                        self.processed_ids.add(tweet.id)
                    
                except RateLimitError as e:
                    # Update rate limits and continue
                    state.x_integration.rate_limits.update({
                        "remaining": e.remaining,
                        "reset_time": e.reset_time,
                        "last_request": datetime.now()
                    })
                    break
            
            # Only monitor influencers if we have enough rate limit remaining
            if state.x_integration.rate_limits["remaining"] > len(self.influencers) * 2:
                for username in self.influencers:
                    try:
                        user, remaining, reset_time = await self.client.get_user_by_username(username)
                        if not user:
                            continue
                            
                        state.x_integration.rate_limits.update({
                            "remaining": remaining,
                            "reset_time": reset_time,
                            "last_request": datetime.now()
                        })
                        
                        tweets, remaining, reset_time = await self.client.get_user_tweets(user['id'], max_results=20)
                        
                        state.x_integration.rate_limits.update({
                            "remaining": remaining,
                            "reset_time": reset_time,
                            "last_request": datetime.now()
                        })
                        
                        for tweet in tweets:
                            if tweet.id in self.processed_ids:
                                continue
                                
                            engagement = self.calculate_engagement(tweet)
                            sentiment = self.calculate_sentiment(tweet.text)
                            
                            # Create social data instance
                            social_data = SocialData(
                                content=tweet.text,
                                timestamp=tweet.created_at,
                                metrics=engagement,
                                author_id=username
                            )
                            
                            # Add to state
                            state.social_data.append(social_data)
                            
                            # Add as event (all influencer posts are events)
                            event = SocialEvent(
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
                            )
                            state.narrative.social_events.append(event.__dict__)
                            state.narrative.pending_analyses = True
                            
                            self.processed_ids.add(tweet.id)
                            
                    except RateLimitError as e:
                        # Update rate limits and break influencer monitoring
                        state.x_integration.rate_limits.update({
                            "remaining": e.remaining,
                            "reset_time": e.reset_time,
                            "last_request": datetime.now()
                        })
                        break
                        
        except Exception as e:
            print(f"Error in social monitoring: {str(e)}")
            state.api_errors.append(f"Social monitoring error: {str(e)}")
        
        return state