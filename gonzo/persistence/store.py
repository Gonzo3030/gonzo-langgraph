from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime
from abc import ABC, abstractmethod
from langchain_core.stores import BaseStore

class PersistentStore(BaseStore[str, Dict[str, Any]]):
    """Base interface for persistent storage.
    
    Provides consistent interface for different storage backends
    while ensuring proper state persistence and recovery.
    """
    
    def __init__(self):
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value by key."""
        pass

    @abstractmethod
    async def mget(self, keys: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Get multiple values by keys."""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Set value by key."""
        pass

    @abstractmethod
    async def mset(
        self,
        key_value_pairs: List[tuple[str, Dict[str, Any]]]
    ) -> None:
        """Set multiple key-value pairs."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value by key."""
        pass

    @abstractmethod
    async def mdelete(self, keys: List[str]) -> None:
        """Delete multiple values by keys."""
        pass
    
    @abstractmethod
    async def list(self, prefix: str = "") -> List[str]:
        """List keys with optional prefix."""
        pass

    @abstractmethod
    async def yield_keys(self, prefix: str = "") -> AsyncIterator[str]:
        """Yield keys with optional prefix."""
        pass

class InMemoryStore(PersistentStore):
    """In-memory implementation of persistent store.
    
    Useful for testing and development.
    """
    
    def __init__(self):
        super().__init__()
        self._data: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get(key)

    async def mget(self, keys: List[str]) -> List[Optional[Dict[str, Any]]]:
        return [self._data.get(k) for k in keys]
    
    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        self._data[key] = value
        self.metadata["last_updated"] = datetime.now().isoformat()

    async def mset(
        self,
        key_value_pairs: List[tuple[str, Dict[str, Any]]]
    ) -> None:
        for key, value in key_value_pairs:
            await self.set(key, value)
    
    async def delete(self, key: str) -> None:
        if key in self._data:
            del self._data[key]
            self.metadata["last_updated"] = datetime.now().isoformat()

    async def mdelete(self, keys: List[str]) -> None:
        for key in keys:
            await self.delete(key)
    
    async def list(self, prefix: str = "") -> List[str]:
        return [
            k for k in self._data.keys()
            if k.startswith(prefix)
        ]

    async def yield_keys(self, prefix: str = "") -> AsyncIterator[str]:
        for key in self._data.keys():
            if key.startswith(prefix):
                yield key