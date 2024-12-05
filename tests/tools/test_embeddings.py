import pytest
import numpy as np
from unittest.mock import Mock, patch
from gonzo.tools.batch_processing.embeddings import EmbeddingProcessor

@pytest.fixture
def embedding_processor():
    with patch('langchain.embeddings.OpenAIEmbeddings') as mock_embeddings:
        processor = EmbeddingProcessor()
        return processor

@pytest.fixture
def mock_run_tree():
    run_tree = Mock()
    run_tree.as_child = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))
    return run_tree

@pytest.mark.asyncio
async def test_get_embeddings(embedding_processor):
    """Test getting embeddings for texts."""
    texts = ["test text 1", "test text 2"]
    
    with patch('langchain.embeddings.OpenAIEmbeddings.aembed_documents') as mock_embed:
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        embeddings = await embedding_processor.get_embeddings(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 2
        mock_embed.assert_called_once_with(texts)

def test_cosine_similarity(embedding_processor):
    """Test cosine similarity calculation."""
    vec1 = [1.0, 0.0]
    vec2 = [1.0, 0.0]
    vec3 = [0.0, 1.0]
    
    # Same vectors should have similarity 1
    assert pytest.approx(embedding_processor.calculate_cosine_similarity(vec1, vec2)) == 1.0
    # Orthogonal vectors should have similarity 0
    assert pytest.approx(embedding_processor.calculate_cosine_similarity(vec1, vec3)) == 0.0