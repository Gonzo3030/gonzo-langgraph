from typing import List, Dict, Any
import numpy as np
from langchain_community.embeddings import OpenAIEmbeddings
from langsmith.run_trees import RunTree

class EmbeddingProcessor:
    """Handles embedding generation and similarity calculations for event batching."""

    def __init__(self, run_tree: RunTree = None):
        self.embeddings = OpenAIEmbeddings()
        self.run_tree = run_tree
        
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts with LangSmith tracking."""
        try:
            if self.run_tree:
                with self.run_tree.as_child('get_embeddings'):
                    embeddings = await self.embeddings.aembed_documents(texts)
            else:
                embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            if self.run_tree:
                self.run_tree.on_error(str(e))
            print(f"Error getting embeddings: {e}")
            return [[0.0] * 1536] * len(texts)  # Return zero embeddings as fallback
            
    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
            
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)