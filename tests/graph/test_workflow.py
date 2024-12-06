import pytest
from gonzo.types import GonzoState

@pytest.mark.asyncio
async def test_workflow_creation(workflow):
    """Test workflow is created successfully."""
    assert workflow is not None

@pytest.mark.asyncio
async def test_market_analysis_path(workflow, initial_state):
    """Test market analysis path through workflow."""
    # Prepare state for market analysis
    state = initial_state.copy()
    state['category'] = 'market'
    state['requires_market_analysis'] = True
    
    # Run workflow
    result = await workflow.invoke(state)
    
    # Verify state was processed
    assert result is not None
    assert isinstance(result, dict)

@pytest.mark.asyncio
async def test_narrative_analysis_path(workflow, initial_state):
    """Test narrative analysis path through workflow."""
    # Prepare state for narrative analysis
    state = initial_state.copy()
    state['category'] = 'narrative'
    state['requires_narrative_analysis'] = True
    
    # Run workflow
    result = await workflow.invoke(state)
    
    # Verify state was processed
    assert result is not None
    assert isinstance(result, dict)

@pytest.mark.asyncio
async def test_state_preservation(workflow, initial_state):
    """Test that state is properly preserved through workflow."""
    # Add test data to state
    test_data = {'test_key': 'test_value'}
    state = initial_state.copy()
    state['category'] = 'market'
    state['context'] = test_data
    
    # Run workflow
    result = await workflow.invoke(state)
    
    # Verify test data was preserved
    assert result['context'] == test_data