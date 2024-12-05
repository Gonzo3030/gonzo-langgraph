import pytest
from datetime import datetime
from langchain.schema import HumanMessage
from gonzo.graph.state import GonzoState, BatchState, MemoryState

@pytest.fixture
def gonzo_state():
    return GonzoState()

def test_state_initialization(gonzo_state):
    """Test that state initializes with correct default values."""
    assert len(gonzo_state.state['messages']) == 0
    assert gonzo_state.state['current_batch'] is None
    assert gonzo_state.state['memory'] is not None
    assert gonzo_state.state['next_step'] == 'initialize'

def test_add_message(gonzo_state):
    """Test adding messages to state."""
    message = HumanMessage(content='Test message')
    gonzo_state.add_message(message)
    
    assert len(gonzo_state.state['messages']) == 1
    assert gonzo_state.state['messages'][0].content == 'Test message'

def test_update_batch(gonzo_state):
    """Test updating batch state."""
    batch: BatchState = {
        'events': [{'id': 1, 'content': 'test'}],
        'batch_id': 'test_batch',
        'timestamp': datetime.now().isoformat(),
        'similarity_score': 0.9
    }
    
    gonzo_state.update_batch(batch)
    assert gonzo_state.state['current_batch'] == batch

def test_memory_operations(gonzo_state):
    """Test memory storage and retrieval."""
    # Test short-term memory
    gonzo_state.save_to_memory('test_key', 'test_value')
    assert gonzo_state.get_from_memory('test_key') == 'test_value'
    
    # Test long-term memory
    gonzo_state.save_to_memory('permanent_key', 'permanent_value', permanent=True)
    assert gonzo_state.get_from_memory('permanent_key', 'long_term') == 'permanent_value'

def test_error_handling(gonzo_state):
    """Test error tracking in state."""
    error_msg = 'Test error'
    gonzo_state.add_error(error_msg)
    
    assert gonzo_state.state['errors'] is not None
    assert len(gonzo_state.state['errors']) == 1
    assert gonzo_state.state['errors'][0] == error_msg

def test_next_step_transition(gonzo_state):
    """Test state transitions."""
    next_step = 'analyze'
    gonzo_state.set_next_step(next_step)
    assert gonzo_state.state['next_step'] == next_step

def test_memory_initialization(gonzo_state):
    """Test memory is properly initialized."""
    assert 'short_term' in gonzo_state.state['memory']
    assert 'long_term' in gonzo_state.state['memory']
    assert 'last_accessed' in gonzo_state.state['memory']

def test_memory_timestamps(gonzo_state):
    """Test that memory operations update timestamps."""
    initial_timestamp = gonzo_state.state['memory']['last_accessed']
    
    # Wait a tiny bit to ensure timestamp difference
    import time
    time.sleep(0.001)
    
    gonzo_state.save_to_memory('test_key', 'test_value')
    new_timestamp = gonzo_state.state['memory']['last_accessed']
    
    assert new_timestamp > initial_timestamp