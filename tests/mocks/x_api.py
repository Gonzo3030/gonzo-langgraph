"""Mock X API for testing."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

class MockTweet:
    """Mock tweet data."""
    def __init__(self):
        self.id = '123456789'
        self.text = 'Test tweet about manipulation patterns'
        self.author_id = '987654321'
        self.conversation_id = '123456789'
        self.created_at = datetime.now(timezone.utc)
        self.referenced_tweets = None
        self.context_annotations = None

class MockUser:
    """Mock user data."""
    def __init__(self):
        self.id = '123456789'
        self.name = 'Gonzo'
        self.username = 'DrGonzo3030'

class MockResponse:
    """Mock API response."""
    def __init__(self, data=None):
        self.data = data

class MockClient:
    """Mock tweepy Client for testing."""
    
    def __init__(self, consumer_key=None, consumer_secret=None, access_token=None,
                 access_token_secret=None):
        self.mock_tweet = MockTweet()
        self.mock_user = MockUser()
    
    def create_tweet(self, text, **kwargs):
        return MockResponse(self.mock_tweet)
    
    def get_me(self, **kwargs):
        return MockResponse(self.mock_user)
    
    def get_users_mentions(self, id, **kwargs):
        return MockResponse([self.mock_tweet])
    
    def search_recent_tweets(self, query, **kwargs):
        return MockResponse([self.mock_tweet])
    
    def get_rate_limit_status(self, **kwargs):
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