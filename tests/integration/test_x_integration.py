"""Integration tests for X API client."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from pytwitter.models import Response, Tweet as ApiTweet, User
from gonzo.integrations.x_client import XClient, Tweet

@pytest.fixture
def mock_tweet_data():
    return ApiTweet(
        id='123456789',
        text='Test tweet about manipulation patterns',
        author_id='987654321',
        conversation_id='123456789',
        created_at=datetime.now(timezone.utc).isoformat() + 'Z',
        referenced_tweets=None,
        context_annotations=None
    )

@pytest.fixture
def mock_user_data():
    return User(
        id='123456789',
        name='Gonzo',
        username='DrGonzo3030'
    )

@pytest.fixture
def x_client():
    return XClient()

@pytest.mark.asyncio
async def test_post_tweet(x_client, mock_tweet_data):
    """Test posting a tweet."""
    mock_response = Response(data=mock_tweet_data)
    with patch('pytwitter.Api.create_tweet', return_value=mock_response):
        response = await x_client.post_tweet("Test tweet")
        assert response.id == mock_tweet_data.id
        assert response.text == mock_tweet_data.text

@pytest.mark.asyncio
async def test_monitor_mentions(x_client, mock_tweet_data, mock_user_data):
    """Test monitoring mentions."""
    mock_tweets_response = Response(data=[mock_tweet_data])
    mock_user_response = Response(data=mock_user_data)
    
    with patch('pytwitter.Api.get_me', return_value=mock_user_response):
        with patch('pytwitter.Api.get_mentions', return_value=mock_tweets_response):
            mentions = await x_client.monitor_mentions()
            assert len(mentions) == 1
            assert isinstance(mentions[0], Tweet)
            assert mentions[0].id == mock_tweet_data.id

@pytest.mark.asyncio
async def test_get_conversation_thread(x_client, mock_tweet_data):
    """Test getting conversation thread."""
    mock_response = Response(data=[mock_tweet_data])
    
    with patch('pytwitter.Api.get_tweets_search_recent', return_value=mock_response):
        thread = await x_client.get_conversation_thread('123456789')
        assert len(thread) == 1
        assert isinstance(thread[0], Tweet)
        assert thread[0].conversation_id == mock_tweet_data.conversation_id

@pytest.mark.asyncio
async def test_monitor_keywords(x_client, mock_tweet_data):
    """Test monitoring keywords."""
    mock_response = Response(data=[mock_tweet_data])
    
    with patch('pytwitter.Api.get_tweets_search_recent', return_value=mock_response):
        tweets = await x_client.monitor_keywords(['test', 'manipulation'])
        assert len(tweets) == 1
        assert isinstance(tweets[0], Tweet)
        assert 'manipulation' in tweets[0].text.lower()

def test_rate_limits(x_client):
    """Test getting rate limits."""
    mock_limits = {'resources': {'tweets': {'/tweets': {'limit': 100, 'remaining': 50}}}}
    
    with patch('pytwitter.Api.get_rate_limit_status', return_value=mock_limits):
        limits = x_client.get_rate_limits()
        assert limits == mock_limits
        assert limits['resources']['tweets']['/tweets']['limit'] == 100