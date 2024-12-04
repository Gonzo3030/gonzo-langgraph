from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime

class TimelineMemory:
    """Structure for timeline-specific memories."""
    def __init__(
        self,
        content: str,
        timestamp: datetime,
        category: str,
        relevance_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.timestamp = timestamp
        self.category = category  # e.g., 'crypto', 'narrative', 'social'
        self.relevance_score = relevance_score
        self.metadata = metadata or {}

class MemoryInterface(ABC):
    """Base interface for Gonzo's memory systems."""
    
    @abstractmethod
    async def get_relevant_memories(
        self,
        query: str,
        category: str,
        timeline: str,
        limit: int = 5
    ) -> List[TimelineMemory]:
        """Retrieve relevant memories for a given query and timeline.
        
        Args:
            query: The current context/query to match memories against
            category: Type of memory (crypto, narrative, etc.)
            timeline: Which timeline to search (pre_1974, dark_period, future)
            limit: Maximum number of memories to return
        """
        pass
    
    @abstractmethod
    async def store_memory(
        self,
        memory: TimelineMemory
    ) -> bool:
        """Store a new memory.
        
        Args:
            memory: The TimelineMemory to store
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def get_timeline_summary(
        self,
        category: str,
        timeline: str
    ) -> str:
        """Get a summary of knowledge for a timeline/category combination.
        
        Args:
            category: Type of memory (crypto, narrative, etc.)
            timeline: Which timeline to summarize
        """
        pass