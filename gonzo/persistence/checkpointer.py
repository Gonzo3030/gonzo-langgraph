from typing import Optional, Dict, Any
from datetime import datetime
from .store import PersistentStore

class Checkpointer:
    """Custom checkpointer for Gonzo state persistence.
    
    Provides:
    - Thread-level persistence
    - State recovery
    - Timeline tracking
    """
    
    def __init__(
        self,
        store: Optional[PersistentStore] = None,
        thread_id: Optional[str] = None
    ):
        """Initialize checkpointer.
        
        Args:
            store: Backend storage implementation
            thread_id: Optional thread identifier
        """
        self.store = store
        self.thread_id = thread_id or datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "last_checkpoint": None
        }
    
    def save(self, checkpoint_data: Dict[str, Any]) -> None:
        """Save checkpoint data (sync version for testing).
        
        Args:
            checkpoint_data: Data to checkpoint
        """
        self.metadata["last_checkpoint"] = datetime.now().isoformat()
        # For testing, we don't actually persist
        pass
        
    async def persist(
        self,
        state: Dict[str, Any],
        *,
        step: int
    ) -> None:
        """Persist state at current step.
        
        Args:
            state: Current state to persist
            step: Current step number
        """
        # Add metadata
        checkpoint = {
            "state": state,
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "thread_id": self.thread_id
        }
        
        # Save checkpoint with step-specific key
        if self.store:
            key = self._make_key(step)
            await self.store.set(key, checkpoint)
            
            # Update metadata
            self.metadata["last_checkpoint"] = key
    
    async def restore(
        self,
        *,
        step: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Restore state from checkpoint.
        
        Args:
            step: Optional specific step to restore
            
        Returns:
            Restored state if available
        """
        if not self.store:
            return None
            
        if step is not None:
            # Restore specific step
            key = self._make_key(step)
        else:
            # Get latest checkpoint
            checkpoints = await self.list_checkpoints()
            if not checkpoints:
                return None
            key = checkpoints[-1]
        
        checkpoint = await self.store.get(key)
        return checkpoint["state"] if checkpoint else None
    
    async def list_checkpoints(self) -> list[str]:
        """List available checkpoints for this thread."""
        if not self.store:
            return []
            
        prefix = f"checkpoint_{self.thread_id}_"
        all_keys = await self.store.list(prefix=prefix)
        
        # Extract step numbers and sort
        def get_step(key: str) -> int:
            # Format: checkpoint_<thread_id>_<step>
            return int(key.split('_')[-1])
            
        return sorted(all_keys, key=get_step)
    
    async def delete(self, step: int) -> None:
        """Delete checkpoint at specific step."""
        if self.store:
            key = self._make_key(step)
            await self.store.delete(key)
    
    async def clear(self) -> None:
        """Clear all checkpoints for this thread."""
        if self.store:
            checkpoints = await self.list_checkpoints()
            await self.store.mdelete(checkpoints)
        
    def _make_key(self, step: int) -> str:
        """Create consistent checkpoint key.
        
        Args:
            step: Step number
            
        Returns:
            Formatted key string
        """
        return f"checkpoint_{self.thread_id}_{step}"