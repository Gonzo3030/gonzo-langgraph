import pytest
from unittest.mock import Mock, patch
from gonzo.states.state_manager import StateManager

@pytest.fixture
def mock_run_tree():
    run_tree = Mock()
    run_tree.as_child = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))
    return run_tree

@pytest.fixture
def state_manager(mock_run_tree):
    return StateManager(run_tree=mock_run_tree)

def test_node_initialization(state_manager, mock_run_tree):
    """Test that nodes are initialized with tracking."""
    # Create mock node with tracking capability
    mock_node = Mock()
    mock_node.set_run_tree = Mock()
    
    with patch('gonzo.states.state_manager.initial_assessment', mock_node):
        manager = StateManager(run_tree=mock_run_tree)
        mock_node.set_run_tree.assert_called_with(mock_run_tree)

@pytest.mark.asyncio
async def test_state_routing(state_manager):
    """Test state routing based on batch results."""
    # Test routing with errors
    state_with_error = {"errors": ["test error"]}
    assert state_manager._determine_next_state(state_with_error) == "response"
    
    # Test routing with high similarity crypto batch
    crypto_state = {
        "context": {"category": "crypto"},
        "current_batch": {"similarity_score": 0.9}
    }
    assert state_manager._determine_next_state(crypto_state) == "crypto"
    
    # Test routing with low similarity
    low_sim_state = {
        "context": {"category": "narrative"},
        "current_batch": {"similarity_score": 0.5}
    }
    assert state_manager._determine_next_state(low_sim_state) == "knowledge"

@pytest.mark.asyncio
async def test_graph_execution(state_manager, mock_run_tree):
    """Test full graph execution with tracking."""
    initial_state = {"test": True}
    
    with patch.object(state_manager.compiled_graph, 'ainvoke') as mock_invoke:
        mock_invoke.return_value = {"result": True}
        result = await state_manager.run(initial_state)
        
        assert result == {"result": True}
        assert mock_run_tree.as_child.called
        mock_invoke.assert_called_with(initial_state)

def test_transition_tracking(state_manager, mock_run_tree):
    """Test that state transitions are properly tracked."""
    state = {
        "context": {"category": "crypto"},
        "current_batch": {"similarity_score": 0.9}
    }
    
    next_state = state_manager._determine_next_state(state)
    assert next_state == "crypto"
    
    # Verify that the transition was tracked
    run_child = mock_run_tree.as_child.return_value.__enter__.return_value
    assert run_child.update_inputs.called
    assert run_child.update_outputs.called