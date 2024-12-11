import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from gonzo.integrations.x.client import XClient
from gonzo.state.x_state import XState

@pytest.fixture
def x_state():
    return XState()

@pytest.fixture
def mock_oauth():
    with patch('gonzo.integrations.x.client.OAuth1Session') as mock:
        mock_session = Mock()
        mock.return_value = mock_session
        yield mock_session

class TestXClient:
    async def test_post_update(self, mock_oauth):
        # Setup
        client = XClient()
        mock_oauth.post.return_value.json.return_value = {
            'data': {'id': '123', 'text': 'Test post'}
        }
        mock_oauth.post.return_value.raise_for_status = Mock()
        
        # Execute
        result = await client.post_update("Test post")
        
        # Assert
        assert result['data']['id'] == '123'
        assert client.daily_counts['posts'] == 1
        mock_oauth.post.assert_called_once()
    
    async def test_post_rate_limit(self, mock_oauth):
        # Setup
        client = XClient()
        client.daily_counts['posts'] = 100  # Max limit
        
        # Execute & Assert
        with pytest.raises(Exception, match="Post limit reached"):
            await client.post_update("Test post")
            
        mock_oauth.post.assert_not_called()
    
    async def test_reply_to_post(self, mock_oauth):
        # Setup
        client = XClient()
        mock_oauth.post.return_value.json.return_value = {
            'data': {'id': '123', 'text': 'Test reply'}
        }
        mock_oauth.post.return_value.raise_for_status = Mock()
        
        # Execute
        result = await client.reply_to_post('456', "Test reply")
        
        # Assert
        assert result['data']['id'] == '123'
        assert client.daily_counts['replies'] == 1
        
        # Verify the correct data was sent
        mock_oauth.post.assert_called_once_with(
            'https://api.twitter.com/2/tweets',
            json={
                'text': 'Test reply',
                'reply': {'in_reply_to_tweet_id': '456'}
            }
        )