"""Integration tests for X API client."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from gonzo.integrations.x_client import XClient, Tweet

@pytest.fixture
def mock_response():
    """Create mock response with test data."""
    class MockResponse:
        def __init__(self, data=None, headers=None):
            self.data = data
            self.headers = headers or {}
            
        def json(self):
            return {"data": self.data}
            
        def raise_for_status(self):
            pass
    return MockResponse

@pytest.fixture
def mock_session(mock_response):
    """Create mock session that returns test data."""
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
    
    class MockSession:
        def get(self, url, **kwargs):
            if "users/me" in url:
                return mock_response(user_data)
            elif "mentions" in url:
                return mock_response([tweet_data])
            elif "search/recent" in url:
                return mock_response([tweet_data], headers={
                    'x-rate-limit-limit': '100',
                    'x-rate-limit-remaining': '50'
                })
            return mock_response()
            
        def post(self, url, **kwargs):
            return mock_response(tweet_data)
    
    return MockSession

@pytest.fixture
def x_client(mock_session):
    """Provide X client with mocked API."""
    with patch('requests_oauthlib.OAuth1Session', mock_session):
        return XClient()

@pytest.mark.asyncio
async def test_post_tweet(x_client):
    """Test posting a tweet."""
    response = await x_client.post_tweet("Test tweet")
    assert response["id"] == "123456789"
    assert "manipulation patterns" in response["text"]

@pytest.mark.asyncio
async def test_monitor_mentions(x_client):
    """Test monitoring mentions."""
    mentions = await x_client.monitor_mentions()
    assert len(mentions) == 1
    assert isinstance(mentions[0], Tweet)
    assert mentions[0].id == "123456789"

@pytest.mark.asyncio
async def test_get_conversation_thread(x_client):
    """Test getting conversation thread."""
    thread = await x_client.get_conversation_thread("123456789")
    assert len(thread) == 1
    assert isinstance(thread[0], Tweet)
    assert thread[0].conversation_id == "123456789"

@pytest.mark.asyncio
async def test_monitor_keywords(x_client):
    """Test monitoring keywords."""
    tweets = await x_client.monitor_keywords(["test", "manipulation"])
    assert len(tweets) == 1
    assert isinstance(tweets[0], Tweet)
    assert "manipulation" in tweets[0].text.lower()

def test_rate_limits(x_client):
    """Test getting rate limits."""
    limits = x_client.get_rate_limits()
    assert limits["resources"]["tweets"]["/tweets"]["limit"] == 100
    assert limits["resources"]["tweets"]["/tweets"]["remaining"] == 50