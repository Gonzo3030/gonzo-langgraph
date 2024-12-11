import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from gonzo.graph.nodes.rag_nodes import RAGNodes
from gonzo.types.base import GonzoState
from gonzo.types.social import Post

@pytest.fixture
def mock_rag():
    """Create mock RAG analyzer."""
    class MockMediaAnalysisRAG:
        def analyze_text(self, text):
            return "Mock analysis: Identified potential manipulation patterns"
    return MockMediaAnalysisRAG()

@pytest.fixture
def sample_state():
    """Create sample state with discovered content."""
    return GonzoState(
        discovered_content=[
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
    )

@pytest.mark.asyncio
async def test_rag_analysis(mock_rag, sample_state):
    """Test RAG analysis of discovered content."""
    # Initialize RAG nodes with mock analyzer
    rag_nodes = RAGNodes()
    rag_nodes.rag = mock_rag
    
    # Run analysis
    result = await rag_nodes.analyze_content(sample_state)
    updated_state = result['state']
    
    # Check analysis results
    assert 'content_analysis' in updated_state.data
    assert len(updated_state.data['content_analysis']) == 2
    
    # Check analysis content
    for post_id, analysis in updated_state.data['content_analysis'].items():
        assert 'timestamp' in analysis
        assert 'content' in analysis
        assert 'analysis' in analysis
        assert 'Mock analysis' in analysis['analysis']

@pytest.mark.asyncio
async def test_unanalyzed_content_tracking(mock_rag, sample_state):
    """Test that we only analyze new content."""
    rag_nodes = RAGNodes()
    rag_nodes.rag = mock_rag
    
    # Add some pre-existing analysis
    sample_state.data['content_analysis'] = {
        "1": {
            'timestamp': datetime.now().isoformat(),
            'content': sample_state.discovered_content[0].dict(),
            'analysis': 'Previous analysis'
        }
    }
    
    # Run analysis
    result = await rag_nodes.analyze_content(sample_state)
    updated_state = result['state']
    
    # Should only have analyzed the new content
    new_analyses = [k for k, v in updated_state.data['content_analysis'].items()
                   if 'Mock analysis' in v['analysis']]
    assert len(new_analyses) == 1
    assert "2" in new_analyses

@pytest.mark.asyncio
async def test_error_handling(mock_rag, sample_state):
    """Test error handling during analysis."""
    rag_nodes = RAGNodes()
    
    # Make the RAG analyzer raise an error
    mock_rag.analyze_text = Mock(side_effect=Exception("Analysis error"))
    rag_nodes.rag = mock_rag
    
    # Run analysis
    result = await rag_nodes.analyze_content(sample_state)
    updated_state = result['state']
    
    # Check error logging
    assert len(updated_state.error_log) > 0
    error_entry = updated_state.error_log[0]
    assert "Analysis error" in error_entry['error']

@pytest.mark.asyncio
async def test_step_logging(mock_rag, sample_state):
    """Test that analysis steps are properly logged."""
    rag_nodes = RAGNodes()
    rag_nodes.rag = mock_rag
    
    # Run analysis
    result = await rag_nodes.analyze_content(sample_state)
    updated_state = result['state']
    
    # Check step logging
    assert len(updated_state.step_log) > 0
    
    # Verify log entries
    rag_steps = [step for step in updated_state.step_log
                if step['step'] == 'rag_analysis']
    assert len(rag_steps) > 0
    
    for step in rag_steps:
        assert 'timestamp' in step
        assert 'data' in step
        assert 'content_id' in step['data']
        assert step['data']['has_analysis'] is True