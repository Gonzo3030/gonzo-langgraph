"""Integration tests for X client."""
import pytest
from unittest.mock import patch, Mock, AsyncMock
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
def oauth_session():
    """Mock OAuth session for testing."""
    with patch('requests_oauthlib.OAuth1Session') as mock:
        mock_session = Mock()
        mock.return_value = mock_session
        yield mock_session

@pytest.fixture
def x_client(oauth_session):
    """Provide configured X client for testing."""
    with patch('gonzo.integrations.x_client.X_API_KEY', 'test_key'), \
         patch('gonzo.integrations.x_client.X_API_SECRET', 'test_secret'), \
         patch('gonzo.integrations.x_client.X_ACCESS_TOKEN', 'test_token'), \
         patch('gonzo.integrations.x_client.X_ACCESS_SECRET', 'test_token_secret'):
        client = XClient()
        return client

@pytest.mark.asyncio
async def test_post_tweet(x_client, oauth_session):
    """Test successful tweet posting."""
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = TWEET_RESPONSE
    mock_response.headers = STANDARD_HEADERS
    mock_response.status_code = 200
    oauth_session.post.return_value = mock_response
    
    response = await x_client.post_tweet("Test tweet")
    
    assert response["id"] == "1234567890"
    assert response["text"] == "Test tweet"

@pytest.mark.asyncio
async def test_monitor_mentions(x_client, oauth_session):
    """Test mentions monitoring."""
    # Mock user ID response
    user_response = Mock()
    user_response.json.return_value = {"data": {"id": "123"}}
    user_response.status_code = 200
    user_response.headers = STANDARD_HEADERS

    # Mock mentions response
    mentions_response = Mock()
    mentions_response.json.return_value = MENTIONS_RESPONSE
    mentions_response.status_code = 200
    mentions_response.headers = STANDARD_HEADERS

    oauth_session.get.side_effect = [user_response, mentions_response]
    
    mentions = await x_client.monitor_mentions()
    
    assert len(mentions) == 1
    assert mentions[0].text == "@gonzo test mention"

@pytest.mark.asyncio
async def test_get_conversation_thread(x_client, oauth_session):
    """Test conversation thread retrieval."""
    mock_response = Mock()
    mock_response.json.return_value = CONVERSATION_RESPONSE
    mock_response.status_code = 200
    mock_response.headers = STANDARD_HEADERS
    oauth_session.get.return_value = mock_response
    
    thread = await x_client.get_conversation_thread("1234567892")
    
    assert len(thread) == 1
    assert thread[0].text == "Test conversation tweet"

@pytest.mark.asyncio
async def test_rate_limit_handling(x_client, oauth_session):
    """Test rate limit handling and retries."""
    # First call hits rate limit, second succeeds
    rate_limit_response = Mock()
    rate_limit_response.status_code = 429
    rate_limit_response.headers = EXHAUSTED_HEADERS
    rate_limit_response.json.return_value = RATE_LIMIT_RESPONSE

    success_response = Mock()
    success_response.status_code = 200
    success_response.headers = STANDARD_HEADERS
    success_response.json.return_value = TWEET_RESPONSE

    oauth_session.post.side_effect = [rate_limit_response, success_response]
    
    response = await x_client.post_tweet("Test tweet")
    
    assert response["id"] == "1234567890"
    assert oauth_session.post.call_count == 2

@pytest.mark.asyncio
async def test_auth_error_handling(x_client, oauth_session):
    """Test authentication error handling."""
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_response.headers = STANDARD_HEADERS
    oauth_session.post.return_value = mock_response
    
    with pytest.raises(AuthenticationError):
        await x_client.post_tweet("Test tweet")

def test_rate_limits(x_client, oauth_session):
    """Test rate limit information."""
    mock_response = Mock()
    mock_response.headers = STANDARD_HEADERS
    mock_response.status_code = 200
    oauth_session.get.return_value = mock_response
    
    limits = x_client.get_rate_limits()
    
    assert limits["/tweets/search/recent"]["limit"] == 100