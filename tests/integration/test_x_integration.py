"""Integration tests for X client."""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timezone
import requests

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

def create_mock_response(status_code, json_data, headers):
    """Create a mock response with the given parameters."""
    mock_response = Mock(spec=requests.Response)
    mock_response.status_code = status_code
    mock_response.headers = headers
    mock_response.json.return_value = json_data
    mock_response.request = Mock(path_url="/tweets")
    return mock_response

@pytest.fixture(autouse=True)
def mock_credentials():
    """Mock API credentials."""
    with patch('gonzo.config.x.X_API_KEY', 'test_key'), \
         patch('gonzo.config.x.X_API_SECRET', 'test_secret'), \
         patch('gonzo.config.x.X_ACCESS_TOKEN', 'test_token'), \
         patch('gonzo.config.x.X_ACCESS_SECRET', 'test_secret'):
        yield

@pytest.fixture
def mock_openapi_agent():
    """Mock OpenAPI agent."""
    agent = Mock()
    agent.rate_limits = {
        "/tweets/search/recent": {"limit": 100, "remaining": 100, "reset": 0}
    }
    return agent

@pytest.fixture(autouse=True)
def mock_requests():
    """Mock all requests."""
    with patch('requests_oauthlib.OAuth1Session') as mock:
        session = Mock()
        mock.return_value = session
        yield session

@pytest.fixture
def x_client(mock_openapi_agent):
    """Create X client instance."""
    return XClient(api_key="test_key", api_agent=mock_openapi_agent)

@pytest.mark.asyncio
async def test_post_tweet(x_client, mock_requests):
    """Test successful tweet posting."""
    mock_requests.post.return_value = create_mock_response(
        200, TWEET_RESPONSE, STANDARD_HEADERS
    )
    
    response = await x_client.post_tweet("Test tweet")
    assert response == TWEET_RESPONSE['data']
    mock_requests.post.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_mentions(x_client, mock_requests):
    """Test mentions monitoring."""
    user_response = create_mock_response(
        200, 
        {"data": {"id": "123"}},
        STANDARD_HEADERS
    )
    mentions_response = create_mock_response(
        200,
        MENTIONS_RESPONSE,
        STANDARD_HEADERS
    )
    mock_requests.get.side_effect = [user_response, mentions_response]
    
    mentions = await x_client.monitor_mentions()
    assert mentions == MENTIONS_RESPONSE['data']
    assert mock_requests.get.call_count == 2

@pytest.mark.asyncio
async def test_get_conversation_thread(x_client, mock_requests):
    """Test conversation thread retrieval."""
    mock_requests.get.return_value = create_mock_response(
        200,
        CONVERSATION_RESPONSE,
        STANDARD_HEADERS
    )
    
    thread = await x_client.get_conversation_thread("1234567892")
    assert thread == CONVERSATION_RESPONSE['data']
    mock_requests.get.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit_handling(x_client, mock_requests):
    """Test rate limit handling and retries."""
    mock_requests.post.return_value = create_mock_response(
        429,
        RATE_LIMIT_RESPONSE,
        EXHAUSTED_HEADERS
    )
    
    with pytest.raises(RateLimitError) as exc:
        await x_client.post_tweet("Test tweet")
    
    assert exc.value.reset_time > 0
    mock_requests.post.assert_called_once()

@pytest.mark.asyncio
async def test_auth_error_handling(x_client, mock_requests):
    """Test authentication error handling."""
    mock_requests.post.return_value = create_mock_response(
        401,
        AUTH_ERROR_RESPONSE,
        STANDARD_HEADERS
    )
    
    with pytest.raises(AuthenticationError):
        await x_client.post_tweet("Test tweet")
    
    mock_requests.post.assert_called_once()

def test_rate_limits(x_client):
    """Test rate limit information."""
    limits = x_client.get_rate_limits()
    assert "/tweets/search/recent" in limits
    assert limits["/tweets/search/recent"]["remaining"] == 100