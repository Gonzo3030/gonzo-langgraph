"""Integration tests for X client."""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timezone
import time

from gonzo.integrations.x_client import XClient, RateLimitError, AuthenticationError
from ..fixtures.x_responses import (
    TWEET_RESPONSE,
    MENTIONS_RESPONSE,
    CONVERSATION_RESPONSE,
    KEYWORD_SEARCH_RESPONSE,
    RATE_LIMIT_RESPONSE,
    AUTH_ERROR_RESPONSE,
    STANDARD_HEADERS,
    EXHAUSTED_HEADERS
)

@pytest.fixture
def mock_session():
    with patch('requests_oauthlib.OAuth1Session') as mock:
        session = Mock()
        mock.return_value = session
        yield session

@pytest.mark.asyncio
async def test_post_tweet(mock_session):
    """Test successful tweet posting."""
    mock_session.post.return_value.json.return_value = TWEET_RESPONSE
    mock_session.post.return_value.headers = STANDARD_HEADERS
    mock_session.post.return_value.status_code = 200
    
    x_client = XClient()
    response = await x_client.post_tweet("Test tweet")
    
    assert response["id"] == "1234567890"
    assert response["text"] == "Test tweet"

@pytest.mark.asyncio
async def test_post_tweet_rate_limit(mock_session):
    """Test tweet posting with rate limit handling."""
    # First call hits rate limit
    mock_session.post.side_effect = [
        Mock(
            status_code=429,
            headers=EXHAUSTED_HEADERS,
            json=lambda: RATE_LIMIT_RESPONSE
        ),
        # Second call succeeds
        Mock(
            status_code=200,
            headers=STANDARD_HEADERS,
            json=lambda: TWEET_RESPONSE
        )
    ]
    
    x_client = XClient()
    response = await x_client.post_tweet("Test tweet")
    
    assert response["id"] == "1234567890"
    assert mock_session.post.call_count == 2

@pytest.mark.asyncio
async def test_monitor_mentions(mock_session):
    """Test mentions monitoring."""
    mock_session.get.return_value.json.return_value = MENTIONS_RESPONSE
    mock_session.get.return_value.headers = STANDARD_HEADERS
    mock_session.get.return_value.status_code = 200
    
    x_client = XClient()
    mentions = await x_client.monitor_mentions()
    
    assert len(mentions) == 1
    assert mentions[0].text == "@gonzo test mention"

@pytest.mark.asyncio
async def test_get_conversation_thread(mock_session):
    """Test conversation thread retrieval."""
    mock_session.get.return_value.json.return_value = CONVERSATION_RESPONSE
    mock_session.get.return_value.headers = STANDARD_HEADERS
    mock_session.get.return_value.status_code = 200
    
    x_client = XClient()
    thread = await x_client.get_conversation_thread("1234567892")
    
    assert len(thread) == 1
    assert thread[0].text == "Test conversation tweet"

@pytest.mark.asyncio
async def test_monitor_keywords(mock_session):
    """Test keyword monitoring."""
    mock_session.get.return_value.json.return_value = KEYWORD_SEARCH_RESPONSE
    mock_session.get.return_value.headers = STANDARD_HEADERS
    mock_session.get.return_value.status_code = 200
    
    x_client = XClient()
    tweets = await x_client.monitor_keywords(["test", "keyword"])
    
    assert len(tweets) == 1
    assert "test keyword" in tweets[0].text.lower()

@pytest.mark.asyncio
async def test_authentication_error(mock_session):
    """Test authentication error handling."""
    mock_session.post.return_value.status_code = 403
    mock_session.post.return_value.text = "Forbidden"
    
    x_client = XClient()
    with pytest.raises(AuthenticationError):
        await x_client.post_tweet("Test tweet")

@pytest.mark.asyncio
async def test_rate_limit_exhaustion(mock_session):
    """Test rate limit exhaustion."""
    # All calls hit rate limit
    mock_session.post.return_value.status_code = 429
    mock_session.post.return_value.headers = EXHAUSTED_HEADERS
    mock_session.post.return_value.json.return_value = RATE_LIMIT_RESPONSE
    
    x_client = XClient()
    with pytest.raises(RateLimitError) as exc:
        await x_client.post_tweet("Test tweet")
    
    assert "Rate limit exceeded" in str(exc.value)
    assert exc.value.reset_time is not None

def test_rate_limits(mock_session):
    """Test rate limit information retrieval."""
    mock_session.get.return_value.headers = STANDARD_HEADERS
    mock_session.get.return_value.status_code = 200
    
    x_client = XClient()
    limits = x_client.get_rate_limits()
    
    assert limits
    assert "/tweets/search/recent" in limits
    assert limits["/tweets/search/recent"]["limit"] == 100
