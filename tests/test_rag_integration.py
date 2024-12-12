import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from gonzo.graph.nodes.rag_nodes import RAGNodes
from gonzo.types.base import GonzoState, NextStep
from gonzo.types.social import Post
from .mocks.llm import MockEmbeddings, MockLLM

@pytest.fixture
def mock_llm():
    """Create mock LLM."""
    return MockLLM()

@pytest.fixture
def mock_embeddings():
    """Create mock embeddings."""
    return MockEmbeddings()

@pytest.fixture
def sample_content():
    """Create sample content for testing."""
    return [
        Post(
            id="1",
            platform="x",
            content="Bitcoin will revolutionize finance! Trust me, everyone's saying it!",
            created_at=datetime.now()
        ),
        Post(
            id="2",
            platform="x",
            content="Breaking: AI companies all agree - regulation is unnecessary.",
            created_at=datetime.now()
        )
    ]

@pytest.fixture
def initial_state(sample_content):
    """Create initial state with discovered content."""
    return GonzoState(
        discovered_content=sample_content,
        next_step=NextStep.RAG
    )

@pytest.mark.asyncio
async def test_rag_analysis(mock_llm, mock_embeddings, initial_state):
    """Test RAG analysis of discovered content."""
    # Initialize RAG nodes in test mode
    rag_nodes = RAGNodes(test_mode=True)
    rag_nodes.init_rag(mock_embeddings=mock_embeddings, mock_llm=mock_llm)
    
    # Run analysis
    result = await rag_nodes.analyze_content(initial_state)
    updated_state = result['state']
    
    # Verify analysis results
    assert 'content_analysis' in updated_state.data
    analysis_results = updated_state.data['content_analysis']
    assert len(analysis_results) == 2
    
    # Check analysis entries
    for content_id in ['1', '2']:
        analysis = analysis_results[content_id]
        assert 'timestamp' in analysis
        assert 'content' in analysis
        assert 'analysis' in analysis
        assert 'Analysis:' in analysis['analysis']

@pytest.mark.asyncio
async def test_unanalyzed_content_tracking(mock_llm, mock_embeddings, initial_state):
    """Test that we only analyze new content."""
    rag_nodes = RAGNodes(test_mode=True)
    rag_nodes.init_rag(mock_embeddings=mock_embeddings, mock_llm=mock_llm)
    
    # Add pre-existing analysis
    initial_state.data['content_analysis'] = {
        "1": {
            'timestamp': datetime.now().isoformat(),
            'content': initial_state.discovered_content[0].model_dump(),
            'analysis': 'Previous analysis'
        }
    }
    
    # Run analysis
    result = await rag_nodes.analyze_content(initial_state)
    updated_state = result['state']
    
    # Should only analyze new content
    analysis_results = updated_state.data['content_analysis']
    assert analysis_results['1']['analysis'] == 'Previous analysis'  # Shouldn't change
    assert 'Analysis:' in analysis_results['2']['analysis']  # New analysis

@pytest.mark.asyncio
async def test_error_handling(mock_embeddings, initial_state):
    """Test error handling during analysis."""
    # Create failing LLM that raises an error
    failing_llm = MockLLM()
    failing_llm._generate = Mock(side_effect=Exception("Mock analysis error"))
    
    # Initialize RAG nodes
    rag_nodes = RAGNodes(test_mode=True)
    rag_nodes.init_rag(mock_embeddings=mock_embeddings, mock_llm=failing_llm)
    
    # Run analysis
    result = await rag_nodes.analyze_content(initial_state)
    updated_state = result['state']
    
    # Verify error was logged
    assert len(updated_state.error_log) > 0
    assert "Mock analysis error" in updated_state.error_log[0]['error']
    
    # Verify state transition was prevented
    assert updated_state.next_step is None

@pytest.mark.asyncio
async def test_workflow_integration(mock_llm, mock_embeddings, initial_state):
    """Test RAG integration in workflow."""
    rag_nodes = RAGNodes(test_mode=True)
    rag_nodes.init_rag(mock_embeddings=mock_embeddings, mock_llm=mock_llm)
    
    # Run analysis
    result = await rag_nodes.analyze_content(initial_state)
    updated_state = result['state']
    
    # Verify state transition
    assert updated_state.next_step == 'assessment'  # Should move to assessment
    
    # Verify analysis results are ready for assessment
    assert 'content_analysis' in updated_state.data
    assert len(updated_state.data['content_analysis']) == 2