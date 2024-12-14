"""Integration tests for X client."""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timezone

from gonzo.integrations.x_client import XClient, RateLimitError, AuthenticationError
from ..fixtures.x_responses import (
    TWEET_RESPONSE,
    MENTIONS_RESPONSE,
    CONVERSATION_RESPONSE,
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
async def test_rate_limit_handling(mock_session):
    """Test rate limit handling and retries."""
    mock_session.post.side_effect = [
        Mock(
            status_code=429,
            headers=EXHAUSTED_HEADERS,
            json=lambda: RATE_LIMIT_RESPONSE
        ),
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
async def test_auth_error_handling(mock_session):
    """Test authentication error handling."""
    mock_session.post.return_value.status_code = 403
    mock_session.post.return_value.text = "Forbidden"
    
    x_client = XClient()
    with pytest.raises(AuthenticationError):
        await x_client.post_tweet("Test tweet")

def test_rate_limits(mock_session):
    """Test rate limit information."""
    mock_session.get.return_value.headers = STANDARD_HEADERS
    mock_session.get.return_value.status_code = 200
    
    x_client = XClient()
    limits = x_client.get_rate_limits()
    
    assert '/tweets/search/recent' in limits
    assert limits['/tweets/search/recent']['limit'] == 100