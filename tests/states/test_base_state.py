import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from gonzo.states.base import BaseState

class TestState(BaseState):
    """Concrete implementation of BaseState for testing."""
    def run(self, state):
        return state

@pytest.fixture
def test_state():
    return TestState()

@pytest.fixture
def mock_run_tree():
    run_tree = Mock()
    run_tree.as_child = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))
    return run_tree

def test_save_to_memory(test_state):
    """Test memory saving with tracking."""
    state = {}
    test_state.set_run_tree(mock_run_tree())
    
    test_state.save_to_memory(state, 'test_key', 'test_value')
    
    assert 'memory' in state
    assert 'test_key' in state['memory']
    assert state['memory']['test_key']['value'] == 'test_value'
    assert 'timestamp' in state['memory']['test_key']

@pytest.mark.asyncio
async def test_process_events(test_state, mock_run_tree):
    """Test event processing with batch processor."""
    test_state.set_run_tree(mock_run_tree)
    events = [{'id': '1', 'content': 'test'}]
    
    with patch('gonzo.tools.batch_processing.processor.BatchProcessor') as mock_batch:
        instance = mock_batch.return_value
        instance.process_batch.return_value.dict.return_value = {'processed': True}
        
        result = await test_state.process_events(events, 'test_category')
        
        assert result == {'processed': True}
        assert instance.add_event.called
        assert instance.process_batch.called

def test_state_validation(test_state, mock_run_tree):
    """Test state validation with tracking."""
    test_state.set_run_tree(mock_run_tree)
    state = {'test': True}
    
    assert test_state.validate_state(state)
    assert mock_run_tree.as_child.called

def test_cleanup(test_state):
    """Test cleanup of resources."""
    test_state.initialize_batch_processor()
    assert test_state.batch_processor is not None
    
    test_state.cleanup()
    assert test_state.batch_processor is None