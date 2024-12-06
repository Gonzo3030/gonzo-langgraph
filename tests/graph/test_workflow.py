import pytest
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from gonzo.types import GonzoState

@pytest.mark.asyncio
async def test_workflow_creation(workflow):
    """Test workflow is created successfully."""
    assert workflow is not None

@pytest.mark.asyncio
async def test_market_analysis_path(workflow, initial_state):
    """Test market analysis path through workflow."""
    # Prepare state for market analysis
    state = dict(initial_state)
    state['category'] = 'market'
    state['requires_market_analysis'] = True
    
    # Run workflow
    result = await workflow.ainvoke(state)
    
    # Verify state was processed
    assert result['market_analysis_completed'] is True
    assert 'market_analysis_timestamp' in result

@pytest.mark.asyncio
async def test_narrative_analysis_path(workflow, initial_state):
    """Test narrative analysis path through workflow."""
    # Prepare state for narrative analysis
    state = dict(initial_state)
    state['category'] = 'narrative'
    state['requires_narrative_analysis'] = True
    
    # Run workflow
    result = await workflow.ainvoke(state)
    
    # Verify state was processed
    assert result['narrative_analysis_completed'] is True
    assert 'narrative_analysis_timestamp' in result

@pytest.mark.asyncio
async def test_state_preservation(workflow, initial_state):
    """Test that state is properly preserved through workflow."""
    # Add test data to state
    test_data = {'test_key': 'test_value'}
    state = dict(initial_state)
    state['category'] = 'market'
    state['context'] = test_data
    
    # Run workflow
    result = await workflow.ainvoke(state)
    
    # Verify test data was preserved
    assert result['context'] == test_data