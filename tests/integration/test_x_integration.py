"""Integration tests for X API client."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from tests.mocks.x_api import MockOAuthSession, MockResponse
from gonzo.integrations.x_client import XClient, Tweet

def get_mock_response(*args, **kwargs):
    """Helper to get appropriate mock response based on URL."""
    url = args[0] if args else kwargs.get('url', '')
    
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
    
    if "/tweets" in url and kwargs.get('json'):
        return MockResponse(json_data={"data": tweet_data})
    elif "users/me" in url:
        return MockResponse(json_data={"data": user_data})
    elif "mentions" in url:
        return MockResponse(json_data={"data": [tweet_data]})
    elif "search/recent" in url:
        return MockResponse(
            json_data={"data": [tweet_data]},
            headers={
                'x-rate-limit-limit': '100',
                'x-rate-limit-remaining': '50'
            }
        )
    return MockResponse()

@pytest.fixture
def x_client():
    """Provide X client with mock API."""
    mock_session = MagicMock()
    mock_session.post = get_mock_response
    mock_session.get = get_mock_response
    
    with patch('requests_oauthlib.OAuth1Session', return_value=mock_session):
        client = XClient()
        return client

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