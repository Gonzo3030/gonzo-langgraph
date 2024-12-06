from typing import Any, Dict, List, Optional, TypeVar, Generic, Tuple, AsyncIterator
from datetime import datetime
import numpy as np
from langchain_core.embeddings import Embeddings
from .base import GonzoBaseStore

class VectorMemoryStore(GonzoBaseStore[str, Dict[str, Any]]):
    """Vector-based memory store for semantic search and pattern matching."""
    
    def __init__(self, embeddings: Embeddings, similarity_threshold: float = 0.3):
        """Initialize vector store.
        
        Args:
            embeddings: LangChain embeddings interface for vector operations
            similarity_threshold: Threshold for pattern matching (default 0.3)
        """
        super().__init__()
        self.embeddings = embeddings
        self.similarity_threshold = similarity_threshold
        self._data: Dict[str, Dict[str, Any]] = {}
        self._vectors: Dict[str, List[float]] = {}
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value by key."""
        entry = self._data.get(key)
        if entry:
            entry["last_accessed"] = datetime.now().isoformat()
        return entry["value"] if entry else None

    async def mget(self, keys: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Get multiple values by keys."""
        return [await self.get(key) for key in keys]
    
    async def set(self, key: str, value: Dict[str, Any], timeline: str = "present") -> None:
        """Set a value with vector embedding."""
        # Get embedding for combined text content
        text_content = self._get_text_content(value)
        text_content += f" {timeline} timeline"  # Add timeline context
        vector = await self.embeddings.aembed_query(text_content)
        
        self._data[key] = {
            "value": value,
            "timeline": timeline,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        self._vectors[key] = vector
        
        self.metadata["total_entries"] = len(self._data)
        await self.update_metadata({"last_updated": datetime.now().isoformat()})

    async def mset(self, key_value_pairs: List[tuple[str, Dict[str, Any]]]) -> None:
        """Set multiple key-value pairs."""
        for key, value in key_value_pairs:
            await self.set(key, value)
    
    async def delete(self, key: str) -> None:
        """Delete a value and its vector by key."""
        if key in self._data:
            del self._data[key]
            del self._vectors[key]
            self.metadata["total_entries"] = len(self._data)
            await self.update_metadata({"last_updated": datetime.now().isoformat()})

    async def mdelete(self, keys: List[str]) -> None:
        """Delete multiple values by keys."""
        for key in keys:
            await self.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return key in self._data
    
    async def list(self) -> List[str]:
        """List all keys."""
        return list(self._data.keys())

    async def yield_keys(self) -> AsyncIterator[str]:
        """Yield all keys."""
        for key in self._data.keys():
            yield key
    
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
    
    async def semantic_search(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for semantically similar entries."""
        query_vector = await self.embeddings.aembed_query(query)
        
        similarities = [
            (key, self._cosine_similarity(query_vector, vec))
            for key, vec in self._vectors.items()
        ]
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return [
            (self._data[key]["value"], score)
            for key, score in similarities[:n_results]
        ]
    
    async def find_patterns(self, pattern_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Find patterns using vector similarity."""
        patterns = []
        
        if pattern_type == "timeline_correlation":
            # Get timeline entries
            present_entries = await self.get_timeline_entries(timeline="present")
            future_entries = await self.get_timeline_entries(timeline="3030")
            
            # Find correlations
            for present in present_entries:
                present_text = self._get_text_content(present) + " present timeline"
                present_vec = await self.embeddings.aembed_query(present_text)
                
                for future in future_entries:
                    future_text = self._get_text_content(future) + " future timeline"
                    future_vec = await self.embeddings.aembed_query(future_text)
                    
                    similarity = self._cosine_similarity(present_vec, future_vec)
                    if similarity > self.similarity_threshold:
                        patterns.append({
                            "type": "timeline_correlation",
                            "present_event": present,
                            "future_event": future,
                            "confidence": float(similarity)
                        })
        
        return patterns
    
    def _get_text_content(self, value: Dict[str, Any]) -> str:
        """Extract text content from a value for embedding."""
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