"""Mock X API response for testing."""

from datetime import datetime, timezone

class MockOAuthSession:
    """Mock OAuth session for testing."""
    def __init__(self, client_key=None, client_secret=None,
                 resource_owner_key=None, resource_owner_secret=None):
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
        
    def post(self, url, json=None, params=None):
        return MockResponse(json_data={"data": self.tweet_data})
        
    def get(self, url, params=None):
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
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")
