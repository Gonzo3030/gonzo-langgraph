from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

class VectorStoreMemory:
    """Vector store for semantic search and retrieval of past interactions."""
    
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []
    
    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        """Add a new memory."""
        self.memories.insert(0, {
            "text": text,
            "metadata": metadata or {}
        })
    
    def get_relevant_memories(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Get relevant memories based on query."""
        # Simple implementation: return most recent memories that match any query term
        query_terms = query.lower().split()
        matching_memories = [
            mem for mem in self.memories
            if any(term in mem["text"].lower() for term in query_terms)
        ]
        return matching_memories[:k] if matching_memories else self.memories[:k]
    
    def clear(self):
        """Clear all memories."""
        self.memories = []