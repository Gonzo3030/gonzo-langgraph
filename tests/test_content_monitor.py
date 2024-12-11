import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from gonzo.integrations.x.monitor import ContentMonitor
from gonzo.state.x_state import XState, MonitoringState
from gonzo.types.social import Post, PostMetrics, QueuedPost

@pytest.fixture
def mock_state():
    return XState(
        monitoring=MonitoringState(
            tracked_topics=["bitcoin", "ai"],
            tracked_users=["resistance_user"]
        )
    )

@pytest.fixture
def content_monitor():
    monitor = ContentMonitor()
    monitor.client = AsyncMock()
    monitor.content_discovery = AsyncMock()
    monitor.content_filter = Mock()
    return monitor

@pytest.mark.asyncio
async def test_monitor_cycle(content_monitor, mock_state):
    """Test full monitoring cycle."""
    # Setup mock discovered content
    discovered_posts = [
        Post(
            id="1",
            platform="x",
            content="Bitcoin analysis",
            created_at=datetime.now(),
            metrics=PostMetrics(likes=100, replies=10)
        )
    ]
    content_monitor.content_discovery.discover_content.return_value = discovered_posts
    
    # Setup mock mentions
    mentions = [
        Post(
            id="2",
            platform="x",
            content="@gonzo what about AI?",
            created_at=datetime.now(),
            metrics=PostMetrics(likes=50, replies=5)
        )
    ]
    content_monitor.client.fetch_mentions.return_value = mentions
    
    # Setup mock filtering
    content_monitor.content_filter.filter_content.return_value = discovered_posts + mentions
    
    # Run monitoring cycle
    all_content = await content_monitor.monitor_cycle(mock_state)
    
    # Verify results
    assert len(all_content) > 0
    assert content_monitor.content_discovery.discover_content.called
    assert content_monitor.client.fetch_mentions.called
    assert content_monitor.content_filter.filter_content.called
    assert mock_state.last_monitor_time is not None

@pytest.mark.asyncio
async def test_process_mentions(content_monitor, mock_state):
    """Test mention processing."""
    # Setup mock mentions
    mentions = [
        Post(
            id="1",
            platform="x",
            content="@gonzo thoughts on crypto?",
            created_at=datetime.now(),
            metrics=PostMetrics(likes=200, replies=30)
        )
    ]
    content_monitor.client.fetch_mentions.return_value = mentions
    
    # Process mentions
    processed_mentions = await content_monitor.process_mentions(mock_state)
    
    # Verify results
    assert len(processed_mentions) > 0
    assert len(mock_state.interaction_queue.pending) > 0
    
    # Check priority calculation
    queued_post = mock_state.interaction_queue.pending[0]
    assert queued_post.priority > 1  # Should have higher priority due to engagement

@pytest.mark.asyncio
async def test_update_metrics(content_monitor, mock_state):
    """Test metrics update functionality."""
    # Add some posts to history
    test_post = Post(
        id="1",
        platform="x",
        content="Test post",
        created_at=datetime.now()
    )
    mock_state.post_history.add_post(test_post)
    
    # Setup mock metrics
    new_metrics = PostMetrics(likes=100, replies=20, reposts=30)
    content_monitor.client.fetch_metrics.return_value = new_metrics
    
    # Update metrics
    await content_monitor.update_metrics(mock_state)
    
    # Verify metrics were updated
    updated_post = mock_state.post_history.posts[0]
    assert updated_post.metrics is not None
    assert updated_post.metrics.likes == new_metrics.likes

def test_priority_calculation(content_monitor):
    """Test interaction priority calculation."""
    # Test high engagement post
    high_engagement = Post(
        id="1",
        platform="x",
        content="Popular post",
        created_at=datetime.now(),
        metrics=PostMetrics(likes=200, replies=50, reposts=100)
    )
    high_priority = content_monitor._calculate_priority(high_engagement)
    
    # Test low engagement post
    low_engagement = Post(
        id="2",
        platform="x",
        content="New post",
        created_at=datetime.now(),
        metrics=PostMetrics(likes=10, replies=2)
    )
    low_priority = content_monitor._calculate_priority(low_engagement)
    
    assert high_priority > low_priority

@pytest.mark.asyncio
async def test_error_handling(content_monitor, mock_state):
    """Test error handling in monitor."""
    # Simulate API error
    content_monitor.client.fetch_mentions.side_effect = Exception("API Error")
    
    # Should handle error gracefully
    mentions = await content_monitor.process_mentions(mock_state)
    
    assert len(mentions) == 0  # Should return empty list on error
    assert len(mock_state.error_log) > 0  # Should log error