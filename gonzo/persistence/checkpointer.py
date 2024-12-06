from typing import Optional, Dict, Any
from datetime import datetime
from .store import PersistentStore

class GonzoCheckpointer:
    """Custom checkpointer for Gonzo state persistence.
    
    Provides:
    - Thread-level persistence
    - State recovery
    - Timeline tracking
    """
    
    def __init__(
        self,
        store: PersistentStore,
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
        
        # Save checkpoint
        key = f"{self.thread_id}_{step}"
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
        if step is not None:
            # Restore specific step
            key = f"{self.thread_id}_{step}"
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
        prefix = f"{self.thread_id}_"
        all_keys = await self.store.list(prefix=prefix)
        return sorted(
            all_keys,
            key=lambda k: int(k.split('_')[1])
        )
    
    async def delete(self, step: int) -> None:
        """Delete checkpoint at specific step."""
        key = f"{self.thread_id}_{step}"
        await self.store.delete(key)
    
    async def clear(self) -> None:
        """Clear all checkpoints for this thread."""
        checkpoints = await self.list_checkpoints()
        await self.store.mdelete(checkpoints)