"""Integration tests for X API client."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from tests.mocks.x_api import MockOAuthSession
from gonzo.integrations.x_client import XClient, Tweet

@pytest.fixture(autouse=True)
def mock_oauth():
    """Mock OAuth session for all tests."""
    with patch('requests_oauthlib.OAuth1Session', MockOAuthSession):
        yield

@pytest.fixture
def x_client():
    """Provide X client for testing."""
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