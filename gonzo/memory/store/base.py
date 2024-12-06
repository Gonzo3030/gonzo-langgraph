from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
from langchain_core.stores import BaseStore

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")

class GonzoBaseStore(BaseStore[KeyType, ValueType], Generic[KeyType, ValueType]):
    """Base store interface for Gonzo's memory system.
    
    Extends LangGraph's BaseStore to add timeline-aware storage capabilities
    and pattern tracking functionality.
    """
    
    def __init__(self):
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_entries": 0
        }
    
    @abstractmethod
    async def get(self, key: KeyType) -> Optional[ValueType]:
        """Get a value by key."""
        pass
    
    @abstractmethod
    async def set(self, key: KeyType, value: ValueType) -> None:
        """Set a value by key."""
        pass
    
    @abstractmethod
    async def delete(self, key: KeyType) -> None:
        """Delete a value by key."""
        pass
    
    @abstractmethod
    async def exists(self, key: KeyType) -> bool:
        """Check if a key exists."""
        pass
    
    @abstractmethod
    async def list(self) -> List[KeyType]:
        """List all keys."""
        pass
    
    @abstractmethod
    async def get_timeline_entries(self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        timeline: str = "present"
    ) -> List[ValueType]:
        """Get entries from a specific timeline period.
        
        Args:
            start_time: Start of time period (optional)
            end_time: End of time period (optional)
            timeline: Which timeline to query (present/1970s/3030)
            
        Returns:
            List of matching entries
        """
        pass
    
    @abstractmethod
    async def find_patterns(self, pattern_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Find patterns of a specific type in the stored data.
        
        Args:
            pattern_type: Type of pattern to look for
            **kwargs: Additional pattern-specific parameters
            
        Returns:
            List of matched patterns with metadata
        """
        pass
    
    async def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update store metadata.
        
        Args:
            updates: Metadata updates to apply
        """
        self.metadata.update(updates)
        self.metadata["last_updated"] = datetime.now().isoformat()