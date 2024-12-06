import pytest
from gonzo.types import GonzoState, create_initial_state
from gonzo.graph.workflow import create_workflow
from langchain_core.messages import HumanMessage

@pytest.fixture
def workflow():
    """Create test workflow instance."""
    return create_workflow()

@pytest.fixture
def initial_state():
    """Create test initial state."""
    return create_initial_state(
        HumanMessage(content="What's happening with Bitcoin today?")
    )

@pytest.mark.asyncio
async def test_workflow_creation(workflow):
    """Test workflow is created successfully."""
    assert workflow is not None

@pytest.mark.asyncio
async def test_market_analysis_flow(workflow, initial_state):
    """Test market analysis path through workflow."""
    # Update state to trigger market analysis
    state = initial_state.copy()
    state['category'] = 'market'
    state['requires_market_analysis'] = True
    
    # Run workflow
    result = await workflow.invoke(state)
    
    # Verify market analysis was triggered
    assert len(result['steps']) > 0
    assert any('market_analysis' in step for step in result['steps'])

@pytest.mark.asyncio
async def test_narrative_analysis_flow(workflow, initial_state):
    """Test narrative analysis path through workflow."""
    # Update state to trigger narrative analysis
    state = initial_state.copy()
    state['category'] = 'narrative'
    state['requires_narrative_analysis'] = True
    
    # Run workflow
    result = await workflow.invoke(state)
    
    # Verify narrative analysis was triggered
    assert len(result['steps']) > 0
    assert any('narrative_analysis' in step for step in result['steps'])

@pytest.mark.asyncio
async def test_causality_analysis_flow(workflow, initial_state):
    """Test causality analysis path through workflow."""
    # Update state to trigger causality analysis
    state = initial_state.copy()
    state['requires_causality_analysis'] = True
    
    # Run workflow
    result = await workflow.invoke(state)
    
    # Verify causality analysis was triggered
    assert len(result['steps']) > 0
    assert any('causality_analysis' in step for step in result['steps'])

@pytest.mark.asyncio
async def test_state_preservation(workflow, initial_state):
    """Test that state is properly preserved through workflow."""
    # Add some test data to state
    state = initial_state.copy()
    state['category'] = 'market'
    state['test_data'] = {'key': 'value'}
    state['requires_market_analysis'] = True
    
    # Run workflow
    result = await workflow.invoke(state)
    
    # Verify state preservation
    assert result['test_data'] == {'key': 'value'}
    assert result['category'] == 'market'
    
@pytest.mark.asyncio
async def test_multiple_analysis_paths(workflow, initial_state):
    """Test that multiple analysis paths can be triggered."""
    # Set up state to trigger multiple analyses
    state = initial_state.copy()
    state['requires_market_analysis'] = True
    state['requires_narrative_analysis'] = True
    
    # Run workflow
    result = await workflow.invoke(state)
    
    # Verify both analyses were triggered
    steps = result['steps']
    assert len(steps) > 1
    assert any('market_analysis' in step for step in steps)
    assert any('narrative_analysis' in step for step in steps)