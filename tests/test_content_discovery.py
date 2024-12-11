import pytest
from datetime import datetime
from gonzo.integrations.x.content_discovery import ContentDiscovery
from gonzo.config.topics import TopicConfiguration
from gonzo.types.social import Post
from gonzo.state.x_state import MonitoringState

def test_topic_configuration():
    """Test that topic configuration contains expected topics."""
    topics = TopicConfiguration.get_all_topics()
    
    # Check for core topics
    assert "Bitcoin" in topics
    assert "Ethereum" in topics
    assert "AI" in topics
    
    # Check we have topics in multiple categories
    categories = TopicConfiguration.get_all_categories()
    assert any(cat.name == "Crypto & DeFi" for cat in categories)
    assert any(cat.name == "Technology & AI" for cat in categories)

@pytest.mark.asyncio
async def test_content_discovery(mock_state):
    """Test that content discovery finds posts for topics."""
    discovery = ContentDiscovery()
    
    # Mock some discovered posts
    mock_posts = [
        Post(
            id="1",
            platform="x",
            content="Bitcoin analysis",
            created_at=datetime.now()
        )
    ]
    
    # Set up mock client
    discovery.client.search_recent = lambda *args, **kwargs: mock_posts
    discovery.client.get_user_posts = lambda *args, **kwargs: []
    
    # Test discovery
    posts = await discovery.discover_content(mock_state)
    assert len(posts) > 0