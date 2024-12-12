from typing import List, Any
from unittest.mock import MagicMock

class MockEmbeddings:
    """Mock embeddings for testing."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return mock embeddings."""
        return [[0.1, 0.2, 0.3] for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Return mock query embedding."""
        return [0.1, 0.2, 0.3]

class MockVectorStore:
    """Mock vector store for testing."""
    def add_texts(self, texts: List[str], metadatas: List[dict] = None):
        """Mock adding texts."""
        pass
    
    def similarity_search(self, query: str, k: int = 4) -> List[Any]:
        """Return mock similar documents."""
        return [{
            'page_content': 'Mock content',
            'metadata': {'source': 'test'}
        }]
    
    @classmethod
    def from_texts(cls, texts: List[str], embedding, metadatas: List[dict] = None):
        """Create mock store."""
        return cls()