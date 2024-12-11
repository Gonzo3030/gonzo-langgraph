import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from gonzo.integrations.x.client import XClient
from gonzo.integrations.x.monitor import ContentMonitor
from gonzo.integrations.x.queue_manager import QueueManager
from gonzo.state.x_state import XState, MonitoringState
from gonzo.types.social import Post, PostMetrics, QueuedPost

@pytest.fixture
def x_state():
    return XState()

@pytest.fixture
def monitoring_state():
    return MonitoringState()

@pytest.fixture
def mock_client():
    with patch('gonzo.integrations.x.client.tweepy.Client') as mock:
        yield mock

class TestXClient:
    async def test_post_update(self, x_state, mock_client):
        # Setup
        client = XClient()
        mock_client.return_value.create_tweet.return_value.data = {'id': '123'}
        post = QueuedPost(content="Test post", priority=1)
        
        # Execute
        posted = await client.post_update(x_state, post)
        
        # Assert
        assert posted.id == '123'
        assert posted.content == "Test post"
        assert posted.platform == 'x'
        assert len(x_state.post_history.posts) == 1
    
    async def test_fetch_metrics(self, x_state, mock_client):
        # Setup
        client = XClient()
        mock_client.return_value.get_tweet.return_value.data.public_metrics = {
            'like_count': 10,
            'reply_count': 5,
            'retweet_count': 3
        }
        
        # Execute
        metrics = await client.fetch_metrics(x_state, '123')
        
        # Assert
        assert metrics.likes == 10
        assert metrics.replies == 5
        assert metrics.reposts == 3

class TestContentMonitor:
    async def test_process_mentions(self, x_state, mock_client):
        # Setup
        monitor = ContentMonitor()
        mock_client.return_value.get_users_mentions.return_value.data = [
            Mock(id='123', text='Test mention', created_at=datetime.now(),
                 author_id='456', public_metrics={
                     'like_count': 1,
                     'reply_count': 0,
                     'retweet_count': 0
                 })
        ]
        
        # Execute
        await monitor.process_mentions(x_state)
        
        # Assert
        assert len(x_state.interaction_queue.pending) == 1
        assert x_state.interaction_queue.pending[0].reply_to_id == '123'

class TestQueueManager:
    async def test_process_post_queue(self, x_state, mock_client):
        # Setup
        manager = QueueManager()
        mock_client.return_value.create_tweet.return_value.data = {'id': '123'}
        post = QueuedPost(content="Test queue post", priority=1)
        x_state.add_to_post_queue(post)
        
        # Execute
        posted = await manager.process_post_queue(x_state)
        
        # Assert
        assert posted.id == '123'
        assert posted.content == "Test queue post"
        assert len(x_state.post_queue) == 0
    
    async def test_process_interaction_queue(self, x_state, mock_client):
        # Setup
        manager = QueueManager()
        mock_client.return_value.create_tweet.return_value.data = {'id': '123'}
        interaction = QueuedPost(
            content="Test reply",
            reply_to_id='456',
            priority=1
        )
        x_state.interaction_queue.add_interaction(interaction)
        
        # Execute
        posted = await manager.process_interaction_queue(x_state)
        
        # Assert
        assert posted.id == '123'
        assert posted.reply_to_id == '456'
        assert len(x_state.interaction_queue.pending) == 0