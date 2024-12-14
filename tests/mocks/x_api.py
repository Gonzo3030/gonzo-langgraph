"""Mock X API response for testing."""

from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import MagicMock

class MockResponse:
    """Mock requests response."""
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {
            'x-rate-limit-limit': '100',
            'x-rate-limit-remaining': '50'
        }
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        pass


class Endpoints:
    """Mock endpoints data."""
    @staticmethod
    def mock_response(url: str, params: Dict[str, Any] = None, json: Dict[str, Any] = None) -> MockResponse:
        tweet_data = {
            "id": "123456789",
            "text": "Test tweet about manipulation patterns",
            "author_id": "987654321",
            "conversation_id": "123456789",
            "created_at": datetime.now(timezone.utc).isoformat() + 'Z',
            "referenced_tweets": None,
            "context_annotations": None
        }
        
        user_data = {
            "id": "987654321",
            "name": "Dr. Gonzo",
            "username": "DrGonzo3030"
        }
        
        if "tweets" in url and json:
            return MockResponse(json_data={"data": tweet_data})
        elif "users/me" in url:
            return MockResponse(json_data={"data": user_data})
        elif "mentions" in url:
            return MockResponse(json_data={"data": [tweet_data]})
        elif "search/recent" in url:
            return MockResponse(json_data={"data": [tweet_data]})
        return MockResponse()

def mock_session():
    """Create mock session with endpoints."""
    session = MagicMock()
    session.get = Endpoints.mock_response
    session.post = Endpoints.mock_response
    return session