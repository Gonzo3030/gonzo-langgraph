from typing import List
from langchain_core.embeddings import Embeddings
import numpy as np

class MockEmbeddings(Embeddings):
    """Mock embeddings provider for testing.
    
    Generates deterministic embeddings based on text content.
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
        
        Uses deterministic vector generation based on text content.
        """
        # Use text content to generate deterministic values
        text_value = sum(ord(c) for c in text)
        rng = np.random.RandomState(text_value)
        
        # Generate base vector
        vec = rng.randn(self.size)
        
        # Add some similarity for related concepts
        if "crypto" in text.lower() or "defi" in text.lower() or "financial" in text.lower():
            vec[0] = 1.0  # Set first dimension to indicate financial domain
        
        # Normalize to unit vector
        return (vec / np.linalg.norm(vec)).tolist()

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async version of embed_documents."""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """Async version of embed_query."""
        return self.embed_query(text)