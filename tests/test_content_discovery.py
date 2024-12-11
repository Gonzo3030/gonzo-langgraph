import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from gonzo.integrations.x.content_discovery import ContentDiscovery
from gonzo.integrations.x.client import XClient
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
    # Create mock client
    mock_client = AsyncMock(spec=XClient)
    
    # Set up mock response
    mock_posts = [
        Post(
            id="1",
            platform="x",
            content="Bitcoin analysis",
            created_at=datetime.now()
        )
    ]
    
    # Configure mock methods
    mock_client.search_recent.return_value = mock_posts
    mock_client.get_user_posts.return_value = []
    
    # Create discovery instance with mock client
    discovery = ContentDiscovery(client=mock_client)
    
    # Test discovery
    posts = await discovery.discover_content(mock_state)
    
    # Verify results
    assert len(posts) > 0
    assert mock_client.search_recent.called