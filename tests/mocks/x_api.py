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
        
    def __dict__(self):
        return {
            'id': self.id,
            'text': self.text,
            'author_id': self.author_id,
            'conversation_id': self.conversation_id,
            'created_at': self.created_at,
            'referenced_tweets': self.referenced_tweets,
            'context_annotations': self.context_annotations
        }

class MockAccount:
    """Mock Twitter account."""
    
    def __init__(self, client=None):
        self.mock_tweet = MockTweet()
    
    def tweet(self, text, **kwargs):
        return self.mock_tweet
    
    def mentions(self, **kwargs):
        return [self.mock_tweet]

class MockClient:
    """Mock Twitter client."""
    
    def __init__(self, consumer_key=None, consumer_secret=None, token=None,
                 token_secret=None):
        self.mock_tweet = MockTweet()
        
    def search_tweets(self, query, **kwargs):
        return [self.mock_tweet]