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
    
    # Check category structure
    categories = TopicConfiguration.get_all_categories()
    assert any(cat.name == "Crypto & DeFi" for cat in categories)
    assert any(cat.name == "Technology & AI" for cat in categories)

def test_content_relevance_scoring():
    """Test basic content relevance scoring."""
    discovery = ContentDiscovery()
    
    # Test crypto content
    crypto_post = Post(
        id="1",
        platform="x",
        content="Bitcoin's role in resisting financial control systems",
        created_at=datetime.now()
    )
    score = discovery._score_content(crypto_post)
    assert score.overall_score > 0.6  # Should be highly relevant
    
    # Test unrelated content
    unrelated_post = Post(
        id="2",
        platform="x",
        content="What's everyone having for lunch today?",
        created_at=datetime.now()
    )
    score = discovery._score_content(unrelated_post)
    assert score.overall_score < 0.6  # Should be less relevant