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
    agent = Mock()
    agent.rate_limits = {
        "/tweets/search/recent": {"limit": 100, "remaining": 100, "reset": 0}
    }
    agent.query_api = Mock()
    return agent

@pytest.fixture
def x_client(mock_llm, mock_openapi_agent):
    """Create X client instance with mocked dependencies."""
    return XClient(api_key="test_key", api_agent=mock_openapi_agent)

@pytest.mark.asyncio
async def test_post_tweet_with_agent(x_client, mock_openapi_agent):
    """Test posting tweet using OpenAPI agent."""
    mock_openapi_agent.query_api.return_value = TWEET_RESPONSE
    
    response = await x_client.post_tweet("Test tweet", use_agent=True)
    assert response == TWEET_RESPONSE.get('data', {})
    mock_openapi_agent.query_api.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_mentions_with_agent(x_client, mock_openapi_agent):
    """Test monitoring mentions using OpenAPI agent."""
    mock_openapi_agent.query_api.side_effect = [
        {"data": {"id": "123"}},
        MENTIONS_RESPONSE
    ]
    
    mentions = await x_client.monitor_mentions(use_agent=True)
    assert mentions == MENTIONS_RESPONSE.get('data', [])
    assert mock_openapi_agent.query_api.call_count == 2
