import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from gonzo.tools.batch_processing.processor import BatchProcessor, EventBatch

@pytest.fixture
def batch_processor():
    return BatchProcessor(
        batch_size=3,
        similarity_threshold=0.8,
        max_batch_wait=30
    )

@pytest.fixture
def mock_run_tree():
    run_tree = Mock()
    run_tree.as_child = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))
    return run_tree

@pytest.mark.asyncio
async def test_add_event(batch_processor):
    """Test adding a single event."""
    event = {
        'id': '1',
        'content': 'Test content',
        'timestamp': datetime.now().timestamp()
    }
    
    await batch_processor.add_event(event, 'test_category')
    assert len(batch_processor.pending_events['test_category']) == 1
    assert batch_processor.pending_events['test_category'][0] == event

@pytest.mark.asyncio
async def test_process_batch(batch_processor, mock_run_tree):
    """Test batch processing with LangSmith tracking."""
    batch_processor.run_tree = mock_run_tree
    events = [
        {'id': '1', 'content': 'Test 1'},
        {'id': '2', 'content': 'Test 2'},
        {'id': '3', 'content': 'Test 3'}
    ]
    
    for event in events:
        await batch_processor.add_event(event, 'test_category')
    
    with patch('gonzo.tools.batch_processing.embeddings.EmbeddingProcessor') as mock_embeddings:
        mock_embeddings.return_value.batch_process_embeddings.return_value = events
        batch = await batch_processor.process_batch('test_category')
        
        assert isinstance(batch, EventBatch)
        assert len(batch.events) > 0
        assert batch.batch_id.startswith('batch_test_category_')
        assert mock_run_tree.as_child.called

@pytest.mark.asyncio
async def test_empty_batch_handling(batch_processor):
    """Test handling of empty categories."""
    result = await batch_processor.process_batch('nonexistent_category')
    assert result is None

@pytest.mark.asyncio
async def test_batch_size_threshold(batch_processor):
    """Test that batches are processed when size threshold is reached."""
    events = [{'id': str(i), 'content': f'Test {i}'} for i in range(3)]
    
    with patch.object(batch_processor, '_process_batch_internal') as mock_process:
        mock_process.return_value = EventBatch(
            events=events,
            batch_id='test_batch',
            checkpoint_id='test_checkpoint',
            similarity_score=0.9
        )
        
        for event in events:
            await batch_processor.add_event(event, 'test_category')
        
        assert mock_process.called
        assert len(batch_processor.pending_events['test_category']) == 0