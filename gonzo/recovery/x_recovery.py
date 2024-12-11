from typing import Optional, Tuple
from datetime import datetime, timedelta
from ..state.x_state import XState
from ..persistence.x_persistence import XPersistence
from ..config.x_config import get_x_config

class XStateRecovery:
    """Handles error recovery and state management for X integration."""
    
    def __init__(self):
        self.persistence = XPersistence()
        self.config = get_x_config()
        self.last_checkpoint: Optional[str] = None
        self.error_counts: dict[str, int] = {}
        self.last_errors: dict[str, datetime] = {}
    
    def should_retry(self, error_type: str) -> bool:
        """Determine if an operation should be retried based on error history."""
        current_count = self.error_counts.get(error_type, 0)
        last_error = self.last_errors.get(error_type)
        
        # If we've exceeded max retries
        if current_count >= self.config.queue_settings['max_retry_attempts']:
            return False
            
        # If we had a recent error, wait for retry delay
        if last_error:
            retry_delay = self.config.queue_settings['retry_delay']
            if datetime.now() - last_error < retry_delay:
                return False
        
        return True
    
    def record_error(self, error_type: str, error_msg: str) -> None:
        """Record an error occurrence."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = datetime.now()
    
    def clear_error_history(self, error_type: str) -> None:
        """Clear error history for successful operations."""
        if error_type in self.error_counts:
            del self.error_counts[error_type]
        if error_type in self.last_errors:
            del self.last_errors[error_type]
    
    async def checkpoint_state(self, state: XState) -> str:
        """Create a checkpoint of the current state."""
        checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all state components
        self.persistence.save_state(state, checkpoint_id)
        self.persistence.save_queues(state, checkpoint_id)
        self.persistence.save_post_history(state.post_history.posts, checkpoint_id)
        
        self.last_checkpoint = checkpoint_id
        return checkpoint_id
    
    async def restore_state(self, checkpoint_id: Optional[str] = None) -> Optional[XState]:
        """Restore state from a checkpoint."""
        # Use last checkpoint if none specified
        if not checkpoint_id:
            checkpoint_id = self.last_checkpoint
        if not checkpoint_id:
            return None
            
        # Load base state
        state = self.persistence.load_state(checkpoint_id)
        if not state:
            return None
            
        # Load queues
        post_queue, pending, processing = self.persistence.load_queues(checkpoint_id)
        state.post_queue = post_queue
        state.interaction_queue.pending = pending
        state.interaction_queue.processing = processing
        
        # Load post history
        posts = self.persistence.load_post_history(checkpoint_id)
        state.post_history.posts = posts
        
        return state
    
    async def handle_queue_error(self, state: XState, error_type: str,
                              error_msg: str) -> Tuple[bool, Optional[str]]:
        """Handle errors in queue processing.
        
        Returns:
            Tuple of (should_retry, error_message)
        """
        self.record_error(error_type, error_msg)
        
        # Check if we should retry
        if self.should_retry(error_type):
            # Create checkpoint before retry
            await self.checkpoint_state(state)
            return True, None
            
        # If we've exceeded retries, checkpoint and return error
        await self.checkpoint_state(state)
        return False, f"Max retries exceeded for {error_type}: {error_msg}"
    
    async def recover_queues(self, state: XState) -> None:
        """Attempt to recover queue state after errors."""
        # Check for items stuck in processing
        current_time = datetime.now()
        retry_delay = self.config.queue_settings['retry_delay']
        
        # Move stuck items back to pending
        for post_id in state.interaction_queue.processing:
            for post in state.post_history.posts:
                if post.id == post_id and \
                   current_time - post.created_at > retry_delay:
                    state.interaction_queue.processing.remove(post_id)
                    # Move back to pending with increased priority
                    state.interaction_queue.add_interaction(
                        QueuedPost(
                            content=post.content,
                            reply_to_id=post.reply_to_id,
                            priority=2,  # Increase priority for retry
                            context={'retry': True}
                        )
                    )
        
        # Checkpoint recovered state
        await self.checkpoint_state(state)
    
    async def initialize_recovery(self) -> Optional[XState]:
        """Initialize system and attempt to recover latest state."""
        # Try to load latest monitoring state
        monitoring_state = self.persistence.load_monitoring_state()
        
        # Find most recent checkpoint
        checkpoints = sorted([
            f for f in os.listdir(f"{self.persistence.base_path}/state")
            if f.endswith('.json') and f != 'monitoring.json'
        ], reverse=True)
        
        if not checkpoints:
            # No checkpoints found, start fresh
            state = XState()
            if monitoring_state:
                state.monitoring_state = monitoring_state
            return state
        
        # Restore from latest checkpoint
        latest_checkpoint = checkpoints[0].replace('.json', '')
        state = await self.restore_state(latest_checkpoint)
        
        if state and monitoring_state:
            state.monitoring_state = monitoring_state
        
        return state