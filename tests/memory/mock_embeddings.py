from typing import List
from langchain_core.embeddings import Embeddings
import numpy as np

class MockEmbeddings(Embeddings):
    """Mock embeddings provider for testing.
    
    Generates consistent, deterministic embeddings based on text content.
    """
    
    def __init__(self, size: int = 10):
        """Initialize mock embeddings.
        
        Args:
            size: Dimension of embedding vectors
        """
        self.size = size
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return [self.embed_query(text) for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Uses hash of text to generate deterministic embedding.
        """
        # Use text hash as seed for reproducibility
        seed = hash(text) % (2**32)
        np.random.seed(seed)
        
        # Generate unit vector
        vec = np.random.randn(self.size)
        return (vec / np.linalg.norm(vec)).tolist()