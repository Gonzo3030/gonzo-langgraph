from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from .types import CausalEvent, TimelineChain

@dataclass
class AnalysisCache:
    """Structure for cached analysis results."""
    timestamp: datetime
    events: Dict[str, CausalEvent]
    chains: Dict[str, TimelineChain]
    metadata: Dict[str, Any]

class CausalAnalysisCheckpointer:
    """Checkpointer for causal analysis state."""
    
    def __init__(self, ttl: int = 3600):
        """Initialize checkpointer.
        
        Args:
            ttl: Time to live for cached entries in seconds (default 1 hour)
        """
        self.cache: Dict[str, AnalysisCache] = {}
        self.ttl = ttl
    
    async def persist(self, key: str, state: Dict[str, Any]) -> None:
        """Save analysis state with timestamp.
        
        Args:
            key: Cache key
            state: State to persist
        """
        cache_entry = AnalysisCache(
            timestamp=datetime.now(),
            events=state.get('events', {}),
            chains=state.get('chains', {}),
            metadata=state.get('metadata', {})
        )
        self.cache[key] = cache_entry
    
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load cached state if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached state if valid, None if expired or missing
        """
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        if (datetime.now() - entry.timestamp).seconds >= self.ttl:
            # Expired - remove and return None
            del self.cache[key]
            return None
            
        return {
            'events': entry.events,
            'chains': entry.chains,
            'metadata': entry.metadata
        }
    
    def generate_key(self, *components: Any) -> str:
        """Generate cache key from components.
        
        Args:
            *components: Values to include in key generation
            
        Returns:
            Cache key string
        """
        # Convert components to strings and join with separator
        key_parts = [str(c) for c in components]
        return "_".join(key_parts)
    
    async def clear_expired(self) -> None:
        """Remove all expired entries from cache."""
        now = datetime.now()
        expired = [
            key for key, entry in self.cache.items()
            if (now - entry.timestamp).seconds >= self.ttl
        ]
        for key in expired:
            del self.cache[key]
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get basic cache statistics.
        
        Returns:
            Dict with cache stats
        """
        return {
            'total_entries': len(self.cache),
            'expired_entries': sum(
                1 for entry in self.cache.values()
                if (datetime.now() - entry.timestamp).seconds >= self.ttl
            )
        }