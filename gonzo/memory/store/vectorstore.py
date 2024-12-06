from typing import Any, Dict, List, Optional, TypeVar, Generic, Tuple
from datetime import datetime
import numpy as np
from langchain_core.embeddings import Embeddings
from .base import GonzoBaseStore, KeyType, ValueType

class VectorMemoryStore(GonzoBaseStore[str, Dict[str, Any]]):
    """Vector-based memory store for semantic search and pattern matching.
    
    Extends base store with vector embeddings for semantic similarity search
    and enhanced pattern recognition capabilities.
    """
    
    def __init__(self, embeddings: Embeddings):
        """Initialize vector store.
        
        Args:
            embeddings: LangChain embeddings interface for vector operations
        """
        super().__init__()
        self.embeddings = embeddings
        self._data: Dict[str, Dict[str, Any]] = {}
        self._vectors: Dict[str, List[float]] = {}
        
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value by key."""
        entry = self._data.get(key)
        if entry:
            entry["last_accessed"] = datetime.now().isoformat()
        return entry["value"] if entry else None
    
    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        timeline: str = "present"
    ) -> None:
        """Set a value with vector embedding.
        
        Args:
            key: Storage key
            value: Value to store
            timeline: Timeline this entry belongs to
        """
        # Get vector embedding for the value
        text_content = self._get_text_content(value)
        vector = await self.embeddings.aembed_query(text_content)
        
        # Store data and vector
        self._data[key] = {
            "value": value,
            "timeline": timeline,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        self._vectors[key] = vector
        
        # Update metadata
        self.metadata["total_entries"] = len(self._data)
        await self.update_metadata({"last_updated": datetime.now().isoformat()})
    
    async def delete(self, key: str) -> None:
        """Delete a value and its vector by key."""
        if key in self._data:
            del self._data[key]
            del self._vectors[key]
            self.metadata["total_entries"] = len(self._data)
            await self.update_metadata({"last_updated": datetime.now().isoformat()})
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return key in self._data
    
    async def list(self) -> List[str]:
        """List all keys."""
        return list(self._data.keys())
    
    async def get_timeline_entries(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        timeline: str = "present"
    ) -> List[Dict[str, Any]]:
        """Get entries from a specific timeline period."""
        entries = []
        for entry in self._data.values():
            if entry["timeline"] != timeline:
                continue
                
            entry_time = datetime.fromisoformat(entry["created_at"])
            if start_time and entry_time < start_time:
                continue
            if end_time and entry_time > end_time:
                continue
                
            entries.append(entry["value"])
        
        return entries
    
    async def find_patterns(self, pattern_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Find patterns using vector similarity.
        
        Supports various pattern types:
        - semantic_similarity: Find semantically similar entries
        - timeline_correlation: Find correlated events across timelines
        - causal_chain: Find potential cause-effect chains
        """
        patterns = []
        
        if pattern_type == "semantic_similarity":
            if "query" in kwargs:
                similar_entries = await self.semantic_search(kwargs["query"])
                patterns.extend([
                    {
                        "type": "semantic_similarity",
                        "entry": entry,
                        "score": score
                    }
                    for entry, score in similar_entries
                ])
                
        elif pattern_type == "timeline_correlation":
            # Enhanced correlation detection using vector similarity
            present_entries = await self.get_timeline_entries(timeline="present")
            future_entries = await self.get_timeline_entries(timeline="3030")
            
            for present in present_entries:
                present_vector = await self.embeddings.aembed_query(
                    self._get_text_content(present)
                )
                
                for future in future_entries:
                    future_vector = await self.embeddings.aembed_query(
                        self._get_text_content(future)
                    )
                    
                    similarity = self._cosine_similarity(
                        present_vector,
                        future_vector
                    )
                    
                    if similarity > 0.7:  # Threshold for correlation
                        patterns.append({
                            "type": "timeline_correlation",
                            "present_event": present,
                            "future_event": future,
                            "confidence": float(similarity)
                        })
        
        return patterns
    
    async def semantic_search(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for semantically similar entries.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of (entry, similarity_score) tuples
        """
        query_vector = await self.embeddings.aembed_query(query)
        
        # Calculate similarities
        similarities = [
            (key, self._cosine_similarity(query_vector, vec))
            for key, vec in self._vectors.items()
        ]
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        return [
            (self._data[key]["value"], score)
            for key, score in similarities[:n_results]
        ]
    
    def _get_text_content(self, value: Dict[str, Any]) -> str:
        """Extract text content from a value for embedding.
        
        Args:
            value: Value to extract text from
            
        Returns:
            Concatenated text content
        """
        # Implement based on your value structure
        # For now, simple concatenation of string values
        return " ".join(
            str(v) for v in value.values()
            if isinstance(v, (str, int, float))
        )
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return float(
            np.dot(vec1, vec2) / (
                np.linalg.norm(vec1) * np.linalg.norm(vec2)
            )
        )