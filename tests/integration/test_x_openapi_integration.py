"""Integration tests for X OpenAPI client."""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timezone
from langchain.llms import BaseLLM
from functools import wraps
import asyncio

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

class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    @property
    def _llm_type(self) -> str:
        """Return identifier of llm."""
        return "mock"
        
    def _generate(self, prompts, stop=None):
        return [{"text": "mocked response"}]

@pytest.fixture
def mock_session():
    """Mock OAuth session."""
    session = Mock()
    session.post = Mock()
    session.get = Mock()
    return session

@pytest.fixture
def mock_oauth(mock_session):
    """Mock OAuth1Session class."""
    with patch('requests_oauthlib.OAuth1Session', return_value=mock_session):
        yield mock_session

@pytest.fixture
def mock_openapi_agent():
    """Mock OpenAPI agent responses."""
    agent = Mock()
    agent.rate_limits = {
        "/tweets/search/recent": {"limit": 100, "remaining": 100, "reset": 0}
    }
    return agent

@pytest.fixture
def x_client(mock_openapi_agent, mock_oauth):
    """Create X client instance with mocked dependencies."""
    client = XClient(api_key="test_key", api_agent=mock_openapi_agent)
    client._session = mock_oauth
    return client

@pytest.mark.asyncio
async def test_post_tweet_with_agent(x_client, mock_openapi_agent):
    """Test posting tweet using OpenAPI agent."""
    mock_openapi_agent.query_api.return_value = TWEET_RESPONSE
    
    response = await x_client.post_tweet("Test tweet", use_agent=True)
    assert response == TWEET_RESPONSE['data']
    mock_openapi_agent.query_api.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_mentions_with_agent(x_client, mock_openapi_agent):
    """Test monitoring mentions using OpenAPI agent."""
    mock_openapi_agent.query_api.side_effect = [
        {"data": {"id": "123"}},
        MENTIONS_RESPONSE
    ]
    
    mentions = await x_client.monitor_mentions(use_agent=True)
    assert mentions == MENTIONS_RESPONSE['data']
    assert mock_openapi_agent.query_api.call_count == 2

@pytest.mark.asyncio
async def test_get_conversation_thread_with_agent(x_client, mock_openapi_agent):
    """Test getting conversation thread using OpenAPI agent."""
    mock_openapi_agent.query_api.return_value = CONVERSATION_RESPONSE
    
    thread = await x_client.get_conversation_thread("1234567892", use_agent=True)
    assert thread == CONVERSATION_RESPONSE['data']
    mock_openapi_agent.query_api.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit_handling_with_agent(x_client, mock_openapi_agent):
    """Test rate limit handling using OpenAPI agent."""
    reset_time = int(datetime.now(timezone.utc).timestamp() + 900)
    mock_openapi_agent.query_api.side_effect = RateLimitError("Rate limit exceeded", reset_time)
    
    with pytest.raises(RateLimitError) as exc:
        await x_client.post_tweet("Test tweet", use_agent=True)
    
    assert exc.value.reset_time == reset_time
    mock_openapi_agent.query_api.assert_called_once()

@pytest.mark.asyncio
async def test_fallback_to_direct_request(x_client, mock_openapi_agent, mock_session):
    """Test fallback to direct request when agent fails."""
    # Make agent fail
    mock_openapi_agent.query_api.side_effect = Exception("Agent failed")
    
    # Set up successful direct request
    mock_session.post.return_value = Mock(
        status_code=200,
        json=lambda: TWEET_RESPONSE,
        headers=STANDARD_HEADERS,
        request=Mock(path_url="/tweets")
    )
    
    response = await x_client.post_tweet("Test tweet", use_agent=True)
    assert response == TWEET_RESPONSE['data']
    assert mock_openapi_agent.query_api.called
    assert mock_session.post.called

def test_health_check_with_agent(x_client, mock_openapi_agent):
    """Test health check using OpenAPI agent."""
    mock_openapi_agent.rate_limits = {
        "/tweets/search/recent": {"limit": 100, "remaining": 100, "reset": 0}
    }
    assert x_client.health_check()
    
    mock_openapi_agent.rate_limits = {
        "/tweets/search/recent": {"limit": 100, "remaining": 0, "reset": 0}
    }
    assert not x_client.health_check()