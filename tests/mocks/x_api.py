"""Mock X API response for testing."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

class MockResponse:
    """Mock requests response."""
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {}
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")

class MockSession(MagicMock):
    """Mock requests session with stored data."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tweet_data = {
            "id": "123456789",
            "text": "Test tweet about manipulation patterns",
            "author_id": "987654321",
            "conversation_id": "123456789",
            "created_at": datetime.now(timezone.utc).isoformat() + 'Z',
            "referenced_tweets": None,
            "context_annotations": None
        }
        
        self.user_data = {
            "id": "987654321",
            "name": "Dr. Gonzo",
            "username": "DrGonzo3030"
        }
        
    def get(self, url, **kwargs):
        if "users/me" in url:
            return MockResponse(json_data={"data": self.user_data})
        elif "mentions" in url:
            return MockResponse(json_data={"data": [self.tweet_data]})
        elif "search/recent" in url:
            return MockResponse(
                json_data={"data": [self.tweet_data]},
                headers={
                    'x-rate-limit-limit': '100',
                    'x-rate-limit-remaining': '50'
                }
            )
        return MockResponse()
        
    def post(self, url, **kwargs):
        return MockResponse(json_data={"data": self.tweet_data})