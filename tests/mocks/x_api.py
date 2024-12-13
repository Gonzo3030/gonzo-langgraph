"""Mock X API for testing."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from pytwitter.models import Response, Tweet, User

class MockXApi:
    """Mock X API client for testing."""
    
    def __init__(self, consumer_key=None, consumer_secret=None, oauth_token=None,
                 oauth_token_secret=None, bearer_token=None):
        self.mock_user = User(
            id='123456789',
            name='Gonzo',
            username='DrGonzo3030'
        )
        
        self.mock_tweet = Tweet(
            id='123456789',
            text='Test tweet about manipulation patterns',
            author_id='987654321',
            conversation_id='123456789',
            created_at=datetime.now(timezone.utc).isoformat() + 'Z',
            referenced_tweets=None,
            context_annotations=None
        )
    
    def create_tweet(self, *args, **kwargs):
        return Response(data=self.mock_tweet)
    
    def get_me(self, *args, **kwargs):
        return Response(data=self.mock_user)
    
    def get_mentions(self, *args, **kwargs):
        return Response(data=[self.mock_tweet])
    
    def get_tweets_search_recent(self, *args, **kwargs):
        return Response(data=[self.mock_tweet])
    
    def get_rate_limit_status(self, *args, **kwargs):
        return {
            'resources': {
                'tweets': {
                    '/tweets': {
                        'limit': 100,
                        'remaining': 50
                    }
                }
            }
        }