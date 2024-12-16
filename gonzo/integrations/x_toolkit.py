"""X integration using Arcade AI toolkit."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from arcade.toolkits.x import XToolkit
from arcade.auth import XAuthProvider

@dataclass
class XPost:
    content: str
    id: str
    created_at: datetime
    metrics: Dict[str, int]
    author_id: str
    context_annotations: List[Dict[str, Any]]

class GonzoXIntegration:
    """Handles X interactions using Arcade AI toolkit."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str
    ):
        # Initialize auth provider
        self.auth = XAuthProvider(
            client_id=api_key,
            client_secret=api_secret,
            access_token=access_token,
            token_secret=access_secret
        )
        
        # Initialize toolkit
        self.toolkit = XToolkit(auth_provider=self.auth)
        
        # Configure monitoring parameters
        self.configure_monitoring()
    
    def configure_monitoring(self):
        """Set up monitoring configuration."""
        self.search_queries = [
            "crypto manipulation market:crypto lang:en -is:retweet",
            "market fraud crypto lang:en -is:retweet",
            "whale alert crypto lang:en -is:retweet",
            "defi hack lang:en -is:retweet"
        ]
        
        self.key_accounts = [
            "whale_alert",
            "cz_binance",
            "VitalikButerin"
        ]
    
    async def post_thread(self, content_list: List[str]) -> Optional[str]:
        """Post a thread of tweets."""
        try:
            # Post initial tweet
            first_tweet = await self.toolkit.create_tweet(
                text=content_list[0],
                reply_settings="mentionedUsers"
            )
            
            last_tweet_id = first_tweet.data.id
            
            # Post the rest of the thread
            for content in content_list[1:]:
                reply = await self.toolkit.create_tweet(
                    text=content,
                    reply_to=last_tweet_id
                )
                last_tweet_id = reply.data.id
                
            return first_tweet.data.id
            
        except Exception as e:
            print(f"Error posting thread: {str(e)}")
            return None
    
    async def monitor_discussions(self) -> List[XPost]:
        """Monitor X for relevant discussions."""
        discussions = []
        
        try:
            # Search recent discussions
            for query in self.search_queries:
                results = await self.toolkit.search_tweets(
                    query=query,
                    max_results=25,
                    tweet_fields=["author_id", "created_at", "public_metrics", "context_annotations"]
                )
                
                if results.data:
                    for tweet in results.data:
                        discussions.append(XPost(
                            content=tweet.text,
                            id=tweet.id,
                            created_at=tweet.created_at,
                            metrics=tweet.public_metrics,
                            author_id=tweet.author_id,
                            context_annotations=tweet.context_annotations
                        ))
        
        except Exception as e:
            print(f"Error monitoring discussions: {str(e)}")
        
        return discussions
    
    async def get_engagement(self, tweet_id: str) -> Dict[str, int]:
        """Get engagement metrics for a tweet."""
        try:
            tweet = await self.toolkit.get_tweet(
                tweet_id,
                tweet_fields=["public_metrics"]
            )
            
            if tweet.data:
                return tweet.data.public_metrics
            
            return {}
            
        except Exception as e:
            print(f"Error getting engagement: {str(e)}")
            return {}
    
    async def monitor_key_accounts(self) -> List[XPost]:
        """Monitor key accounts for relevant posts."""
        posts = []
        
        try:
            for username in self.key_accounts:
                # Get user ID
                user = await self.toolkit.get_user_by_username(username)
                if not user.data:
                    continue
                    
                # Get recent tweets
                tweets = await self.toolkit.get_user_tweets(
                    user.data.id,
                    max_results=10,
                    tweet_fields=["created_at", "public_metrics", "context_annotations"]
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        posts.append(XPost(
                            content=tweet.text,
                            id=tweet.id,
                            created_at=tweet.created_at,
                            metrics=tweet.public_metrics,
                            author_id=user.data.id,
                            context_annotations=tweet.context_annotations
                        ))
                        
        except Exception as e:
            print(f"Error monitoring key accounts: {str(e)}")
        
        return posts