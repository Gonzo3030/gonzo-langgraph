import tweepy
import logging
from typing import Dict, List, Optional
from time import sleep

logger = logging.getLogger(__name__)

class XClient:
    def __init__(self, credentials: Dict[str, str]):
        """Initialize X client with API credentials."""
        self.auth = tweepy.OAuthHandler(
            credentials['api_key'],
            credentials['api_secret']
        )
        self.auth.set_access_token(
            credentials['access_token'],
            credentials['access_secret']
        )
        self.api = tweepy.API(self.auth)
        self.client = tweepy.Client(
            consumer_key=credentials['api_key'],
            consumer_secret=credentials['api_secret'],
            access_token=credentials['access_token'],
            access_token_secret=credentials['access_secret']
        )
        
    def post_tweet(self, text: str, reply_to: Optional[str] = None) -> Dict:
        """Post a tweet, optionally as a reply."""
        try:
            if reply_to:
                response = self.client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=reply_to
                )
            else:
                response = self.client.create_tweet(text=text)
            
            return {'id': response.data['id'], 'text': text}
            
        except Exception as e:
            logger.error(f'Failed to post tweet: {str(e)}')
            raise
    
    def get_mentions(self, since_id: Optional[str] = None) -> List[Dict]:
        """Get recent mentions of the bot."""
        try:
            mentions = []
            for tweet in tweepy.Paginator(
                self.client.get_users_mentions,
                since_id=since_id,
                max_results=100
            ).flatten(limit=1000):
                mentions.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'author_id': tweet.author_id,
                    'conversation_id': tweet.conversation_id
                })
            return mentions
            
        except Exception as e:
            logger.error(f'Failed to get mentions: {str(e)}')
            raise
    
    def get_conversation_thread(self, tweet_id: str) -> List[Dict]:
        """Get full conversation thread for a tweet."""
        try:
            conversation = []
            # Get the conversation ID first
            tweet = self.client.get_tweet(
                tweet_id,
                expansions=['conversation_id']
            )
            conversation_id = tweet.data.conversation_id
            
            # Get all tweets in conversation
            for tweet in tweepy.Paginator(
                self.client.search_recent_tweets,
                query=f'conversation_id:{conversation_id}',
                max_results=100
            ).flatten(limit=1000):
                conversation.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'author_id': tweet.author_id
                })
            
            return conversation
            
        except Exception as e:
            logger.error(f'Failed to get conversation: {str(e)}')
            raise
    
    def handle_rate_limit(self, wait_time: int = 60):
        """Handle rate limit by waiting."""
        logger.warning(f'Rate limit hit, waiting {wait_time} seconds')
        sleep(wait_time)
