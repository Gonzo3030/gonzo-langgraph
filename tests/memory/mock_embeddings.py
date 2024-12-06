from typing import List
from langchain_core.embeddings import Embeddings
import numpy as np

class MockEmbeddings(Embeddings):
    """Mock embeddings provider for testing.
    
    Generates deterministic embeddings that maintain semantic relationships.
    """
    
    def __init__(self, size: int = 10):
        """Initialize mock embeddings.
        
        Args:
            size: Dimension of embedding vectors
        """
        self.size = size
        # Define base vectors for different domains
        self._base_vectors = {
            'crypto': self._create_base_vector('crypto'),
            'finance': self._create_base_vector('finance'),
            'defi': self._create_base_vector('defi'),
            'future': self._create_base_vector('future'),
            'present': self._create_base_vector('present')
        }
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return [self.embed_query(text) for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Creates embeddings that maintain semantic relationships between
        related concepts and timelines.
        """
        text = text.lower()
        
        # Initialize vector
        vec = np.zeros(self.size)
        
        # Add domain components
        if any(term in text for term in ['crypto', 'bitcoin', 'currency']):
            vec += self._base_vectors['crypto']
        if any(term in text for term in ['finance', 'financial', 'market']):
            vec += self._base_vectors['finance']
        if any(term in text for term in ['defi', 'decentralized']):
            vec += self._base_vectors['defi']
            
        # Add timeline components
        if any(term in text for term in ['future', '3030', 'will']):
            vec += self._base_vectors['future']
        if any(term in text for term in ['present', 'current', 'now']):
            vec += self._base_vectors['present']
            
        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            # Random fallback if no components matched
            vec = self._create_base_vector(text)
        
        return vec.tolist()

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async version of embed_documents."""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """Async version of embed_query."""
        return self.embed_query(text)
        
    def _create_base_vector(self, seed: str) -> np.ndarray:
        """Create a deterministic base vector for a concept."""
        rng = np.random.RandomState(hash(seed) % (2**32))
        vec = rng.randn(self.size)
        return vec / np.linalg.norm(vec)