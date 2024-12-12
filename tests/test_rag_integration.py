import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from gonzo.graph.nodes.rag_nodes import RAGNodes
from gonzo.types.base import GonzoState, NextStep
from gonzo.types.social import Post

@pytest.fixture
def mock_rag():
    """Create mock RAG analyzer."""
    class MockMediaAnalysisRAG:
        def analyze_text(self, text: str) -> str:
            if 'Bitcoin' in text:
                return "Analysis: Potential narrative manipulation around cryptocurrency adoption"
            elif 'AI' in text:
                return "Analysis: Appeal to authority pattern in AI regulation discussion"
            return "Analysis: No clear manipulation patterns detected"
    return MockMediaAnalysisRAG()

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
async def test_rag_analysis(mock_rag, initial_state):
    """Test RAG analysis of discovered content."""
    # Initialize RAG nodes with mock analyzer
    rag_nodes = RAGNodes()
    rag_nodes.rag = mock_rag
    
    # Run analysis
    result = await rag_nodes.analyze_content(initial_state)
    updated_state = result['state']
    
    # Verify analysis results
    assert 'content_analysis' in updated_state.data
    analysis_results = updated_state.data['content_analysis']
    assert len(analysis_results) == 2
    
    # Check Bitcoin content analysis
    bitcoin_analysis = analysis_results['1']
    assert 'cryptocurrency' in bitcoin_analysis['analysis'].lower()
    
    # Check AI content analysis
    ai_analysis = analysis_results['2']
    assert 'authority' in ai_analysis['analysis'].lower()
    
    # Verify step logging
    rag_steps = [step for step in updated_state.step_log
                if step['step'] == 'rag_analysis']
    assert len(rag_steps) == 2

@pytest.mark.asyncio
async def test_unanalyzed_content_tracking(mock_rag, initial_state):
    """Test that we only analyze new content."""
    rag_nodes = RAGNodes()
    rag_nodes.rag = mock_rag
    
    # Add pre-existing analysis
    initial_state.data['content_analysis'] = {
        "1": {
            'timestamp': datetime.now().isoformat(),
            'content': initial_state.discovered_content[0].dict(),
            'analysis': 'Previous analysis'
        }
    }
    
    # Run analysis
    result = await rag_nodes.analyze_content(initial_state)
    updated_state = result['state']
    
    # Should only analyze new content
    new_analyses = [k for k, v in updated_state.data['content_analysis'].items()
                   if v['analysis'].startswith('Analysis:')]
    assert len(new_analyses) == 1
    assert "2" in new_analyses

@pytest.mark.asyncio
async def test_error_handling(mock_rag, initial_state):
    """Test error handling during analysis."""
    rag_nodes = RAGNodes()
    
    # Make RAG analyzer raise an error
    mock_rag.analyze_text = Mock(side_effect=Exception("Analysis error"))
    rag_nodes.rag = mock_rag
    
    # Run analysis
    result = await rag_nodes.analyze_content(initial_state)
    updated_state = result['state']
    
    # Verify error logging
    assert len(updated_state.error_log) > 0
    assert "Analysis error" in updated_state.error_log[0]['error']