import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from gonzo.integrations.x.content_discovery import ContentDiscovery, ContentRelevanceScore
from gonzo.config.topics import TopicConfiguration
from gonzo.types.social import Post, PostMetrics

# Import our test state models instead of the real ones
from .conftest import TestMonitoringState as MonitoringState

@pytest.fixture
def mock_client():
    return AsyncMock()

@pytest.fixture
def mock_state():
    return MonitoringState(
        tracked_topics=["bitcoin", "ai"],
        tracked_users=["resistance_user"],
        last_check_times={},
        current_trends=["crypto", "tech"],
        last_trends_update=datetime.now() - timedelta(hours=2)
    )

@pytest.fixture
def content_discovery(mock_client):
    discovery = ContentDiscovery(client=mock_client)
    return discovery

def test_topic_configuration():
    """Test that topic configuration contains expected categories."""
    categories = TopicConfiguration.get_all_categories()
    assert len(categories) > 0
    
    # Check for core categories
    category_names = [cat.name for cat in categories]
    assert "Crypto & DeFi" in category_names
    assert "Technology & AI" in category_names
    
    # Check priority levels
    crypto_defi = TopicConfiguration.CRYPTO_DEFI
    assert crypto_defi.priority == 5  # Should be highest priority

def test_content_relevance_scoring():
    """Test content relevance scoring logic."""
    discovery = ContentDiscovery()
    
    # Test highly relevant content
    relevant_post = Post(
        id="123",
        platform="x",
        content="Bitcoin and cryptocurrency are tools for resistance against centralized control",
        created_at=datetime.now(),
        metrics=PostMetrics(likes=100, replies=10)
    )
    score = discovery._score_content(relevant_post)
    assert score.topic_match > 0.0
    assert score.overall_score > 0.0
    
    # Test less relevant content
    irrelevant_post = Post(
        id="456",
        platform="x",
        content="Just had a great lunch!",
        created_at=datetime.now(),
        metrics=PostMetrics(likes=5, replies=1)
    )
    score = discovery._score_content(irrelevant_post)
    assert score.overall_score < score.topic_match  # Should score lower

@pytest.mark.asyncio
async def test_discover_content(content_discovery, mock_state):
    """Test the main content discovery process."""
    # Mock some discovered posts
    mock_posts = [
        Post(
            id="1",
            platform="x",
            content="Bitcoin price analysis and decentralization impact",
            created_at=datetime.now(),
            metrics=PostMetrics(likes=150, replies=20)
        ),
        Post(
            id="2",
            platform="x",
            content="AI developments in autonomous systems",
            created_at=datetime.now(),
            metrics=PostMetrics(likes=120, replies=15)
        )
    ]
    
    # Setup mock responses
    content_discovery.client.search_recent = AsyncMock(return_value=mock_posts)
    content_discovery.client.get_user_posts = AsyncMock(return_value=mock_posts)
    
    # Test discovery process
    discovered_posts = await content_discovery.discover_content(mock_state)
    
    assert len(discovered_posts) > 0
    # Check if discovered posts are properly scored and filtered
    for post in discovered_posts:
        score = content_discovery._score_content(post)
        assert score.overall_score >= 0.6  # Should meet minimum threshold

@pytest.mark.asyncio
async def test_category_content_discovery(content_discovery, mock_state):
    """Test content discovery for specific categories."""
    mock_posts = [
        Post(
            id="1",
            platform="x",
            content="DeFi and cryptocurrency updates",
            created_at=datetime.now(),
            metrics=PostMetrics(likes=200, replies=30)
        )
    ]
    content_discovery.client.search_recent = AsyncMock(return_value=mock_posts)
    
    # Test crypto category
    category_posts = await content_discovery._get_category_content(
        TopicConfiguration.CRYPTO_DEFI,
        mock_state
    )
    
    assert len(category_posts) > 0
    assert content_discovery.client.search_recent.called

@pytest.mark.asyncio
async def test_error_handling(content_discovery, mock_state):
    """Test error handling in content discovery."""
    # Simulate API error
    content_discovery.client.search_recent = AsyncMock(side_effect=Exception("API Error"))
    
    # Should handle error gracefully and log it
    with pytest.raises(Exception):
        await content_discovery._get_category_content(
            TopicConfiguration.CRYPTO_DEFI,
            mock_state
        )
        
    # Verify error was logged
    assert len(mock_state.error_log) > 0