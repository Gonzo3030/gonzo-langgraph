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
        # Define semantic components
        rng = np.random.RandomState(42)  # Fixed seed for determinism
        self._components = {
            # Domain components (first half of vector)
            'crypto': rng.randn(size // 2),
            'finance': rng.randn(size // 2),
            'defi': rng.randn(size // 2),
            
            # Timeline components (second half of vector)
            'future': np.concatenate([np.zeros(size // 2), rng.randn(size // 2)]),
            'present': np.concatenate([np.zeros(size // 2), -rng.randn(size // 2)])
        }
        
        # Normalize all components
        for key in self._components:
            self._components[key] = self._normalize(self._components[key])
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return [self.embed_query(text) for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Creates embeddings that maintain semantic relationships between
        related concepts and timelines.
        """
        text = text.lower()
        vec = np.zeros(self.size)
        
        # Add domain components (with higher weight)
        domain_weight = 0.6
        if any(term in text for term in ['crypto', 'bitcoin', 'cryptocurrency']):
            vec += domain_weight * self._components['crypto']
        if any(term in text for term in ['finance', 'financial', 'market']):
            vec += domain_weight * self._components['finance']
        if any(term in text for term in ['defi', 'decentralized']):
            vec += domain_weight * self._components['defi']
            
        # Add timeline components
        timeline_weight = 0.4
        if any(term in text for term in ['future', '3030', 'will', 'becomes']):
            vec += timeline_weight * self._components['future']
        if any(term in text for term in ['present', 'current', 'now', 'adoption']):
            vec += timeline_weight * self._components['present']
            
        # Ensure vector is normalized
        return self._normalize(vec).tolist()

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async version of embed_documents."""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """Async version of embed_query."""
        return self.embed_query(text)
    
    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        """Normalize vector to unit length."""
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec