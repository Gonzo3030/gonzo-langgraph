"""Integration tests for X OpenAPI client."""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timezone
from langchain.llms import BaseLLM

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
    def _generate(self, prompts, stop=None):
        return [{"text": "mocked response"}]

@pytest.fixture
def mock_llm():
    return MockLLM()

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
    """Mock OpenAPI agent responses."""
    with patch('gonzo.api.openapi_agent.OpenAPIAgentTool') as mock:
        agent = Mock()
        mock.return_value = agent
        yield agent

@pytest.fixture
def x_client(mock_llm, mock_openapi_agent):
    """Create X client instance with mocked dependencies."""
    return XClient(llm=mock_llm)

@pytest.mark.asyncio
async def test_post_tweet_with_agent(x_client, mock_openapi_agent):
    """Test posting tweet using OpenAPI agent."""
    mock_openapi_agent.query_api.return_value = TWEET_RESPONSE["data"]
    
    response = await x_client.post_tweet("Test tweet", use_agent=True)
    assert response["id"] == "1234567890"
    assert response["text"] == "Test tweet"
    mock_openapi_agent.query_api.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_mentions_with_agent(x_client, mock_openapi_agent):
    """Test monitoring mentions using OpenAPI agent."""
    mock_openapi_agent.query_api.side_effect = [
        {"data": {"id": "123"}},  # User ID response
        MENTIONS_RESPONSE  # Mentions response
    ]
    
    mentions = await x_client.monitor_mentions(use_agent=True)
    assert len(mentions) == 1
    assert mentions[0].text == "@gonzo test mention"
    assert mock_openapi_agent.query_api.call_count == 2

@pytest.mark.asyncio
async def test_get_conversation_thread_with_agent(x_client, mock_openapi_agent):
    """Test getting conversation thread using OpenAPI agent."""
    mock_openapi_agent.query_api.return_value = CONVERSATION_RESPONSE
    
    thread = await x_client.get_conversation_thread("1234567892", use_agent=True)
    assert len(thread) == 1
    assert thread[0].text == "Test conversation tweet"
    mock_openapi_agent.query_api.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit_handling_with_agent(x_client, mock_openapi_agent):
    """Test rate limit handling using OpenAPI agent."""
    mock_openapi_agent.query_api.side_effect = RateLimitError("Rate limit exceeded", 1234567890)
    
    with pytest.raises(RateLimitError) as exc:
        await x_client.post_tweet("Test tweet", use_agent=True)
    
    assert exc.value.reset_time == 1234567890
    mock_openapi_agent.query_api.assert_called_once()

@pytest.mark.asyncio
async def test_fallback_to_direct_request(x_client, mock_openapi_agent):
    """Test fallback to direct request when agent fails."""
    # Make agent fail
    mock_openapi_agent.query_api.side_effect = Exception("Agent failed")
    
    # Mock direct request success
    with patch('requests_oauthlib.OAuth1Session') as mock_session:
        session = Mock()
        mock_session.return_value = session
        session.post.return_value.json.return_value = TWEET_RESPONSE
        session.post.return_value.headers = STANDARD_HEADERS
        session.post.return_value.status_code = 200
        
        response = await x_client.post_tweet("Test tweet", use_agent=True)
        
        assert response["id"] == "1234567890"
        assert mock_openapi_agent.query_api.called
        assert session.post.called

def test_health_check_with_agent(x_client, mock_openapi_agent):
    """Test health check using OpenAPI agent."""
    mock_openapi_agent.rate_limits = {"x": {"remaining": 100}}
    
    assert x_client.health_check()
    
    mock_openapi_agent.rate_limits = {"x": {"remaining": 0}}
    assert not x_client.health_check()