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
        # Define semantic components with full vector size
        rng = np.random.RandomState(42)  # Fixed seed for determinism
        
        # Create base vectors for each concept
        self._components = {}
        
        # Shared financial domain vector (common to crypto/defi concepts)
        financial_vec = np.zeros(size)
        financial_vec[:size//2] = rng.randn(size//2)
        self._components['financial'] = self._normalize(financial_vec)
        
        # Domain components - all share financial base with variations
        for domain in ['crypto', 'defi']:
            vec = self._components['financial'].copy()
            # Add domain-specific variation
            variation = np.zeros(size)
            variation[:size//2] = rng.randn(size//2) * 0.5
            vec += variation
            self._components[domain] = self._normalize(vec)
        
        # Timeline components (emphasized in second half)
        future_vec = np.zeros(size)
        future_vec[size//2:] = np.array([1.0, 1.0, -1.0, 1.0, 1.0])  # Fixed pattern
        self._components['future'] = self._normalize(future_vec)
        
        present_vec = np.zeros(size)
        present_vec[size//2:] = np.array([-1.0, -1.0, 1.0, -1.0, -1.0])  # Opposite pattern
        self._components['present'] = self._normalize(present_vec)
    
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
        
        # Start with financial domain if relevant
        if any(term in text for term in ['finance', 'financial', 'market', 'crypto', 'defi']):
            vec += self._components['financial']
        
        # Add specific domain components
        if any(term in text for term in ['crypto', 'bitcoin', 'cryptocurrency']):
            vec += self._components['crypto']
        if any(term in text for term in ['defi', 'decentralized']):
            vec += self._components['defi']
            
        # Add timeline components with strong weighting
        if any(term in text for term in ['future', '3030', 'will', 'becomes']):
            vec += self._components['future'] * 2
        if any(term in text for term in ['present', 'current', 'now', 'adoption']):
            vec += self._components['present'] * 2
        
        # Add more weight to empty vectors to avoid zero division
        if np.all(vec == 0):
            vec = np.random.RandomState(hash(text)).randn(self.size)
            
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
        # Fallback for zero vectors
        vec = np.random.RandomState(0).randn(self.size)
        return vec / np.linalg.norm(vec)