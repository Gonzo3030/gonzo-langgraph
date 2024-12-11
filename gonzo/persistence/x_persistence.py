from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
from ..state.x_state import XState, MonitoringState
from ..types.social import Post, PostMetrics, QueuedPost

class XPersistence:
    """Handles persistence for X integration state and queues."""
    
    def __init__(self, base_path: str = "./data/x"):
        self.base_path = base_path
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            self.base_path,
            f"{self.base_path}/queues",
            f"{self.base_path}/history",
            f"{self.base_path}/state"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _serialize_datetime(self, obj: Any) -> Any:
        """Handle datetime serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def _deserialize_datetime(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Handle datetime deserialization."""
        for key, value in obj.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    obj[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
            elif isinstance(value, dict):
                obj[key] = self._deserialize_datetime(value)
        return obj
    
    def save_state(self, state: XState, checkpoint_id: str) -> None:
        """Save X state to disk."""
        state_path = f"{self.base_path}/state/{checkpoint_id}.json"
        
        # Convert state to dict and serialize
        state_dict = state.dict()
        
        with open(state_path, 'w') as f:
            json.dump(state_dict, f, default=self._serialize_datetime)
    
    def load_state(self, checkpoint_id: str) -> Optional[XState]:
        """Load X state from disk."""
        state_path = f"{self.base_path}/state/{checkpoint_id}.json"
        
        if not os.path.exists(state_path):
            return None
            
        with open(state_path, 'r') as f:
            state_dict = json.load(f)
            
        # Handle datetime fields
        state_dict = self._deserialize_datetime(state_dict)
        
        return XState.parse_obj(state_dict)
    
    def save_monitoring_state(self, state: MonitoringState) -> None:
        """Save monitoring state to disk."""
        state_path = f"{self.base_path}/state/monitoring.json"
        
        state_dict = state.dict()
        
        with open(state_path, 'w') as f:
            json.dump(state_dict, f, default=self._serialize_datetime)
    
    def load_monitoring_state(self) -> Optional[MonitoringState]:
        """Load monitoring state from disk."""
        state_path = f"{self.base_path}/state/monitoring.json"
        
        if not os.path.exists(state_path):
            return None
            
        with open(state_path, 'r') as f:
            state_dict = json.load(f)
            
        state_dict = self._deserialize_datetime(state_dict)
        return MonitoringState.parse_obj(state_dict)
    
    def save_post_history(self, posts: list[Post], checkpoint_id: str) -> None:
        """Save post history to disk."""
        history_path = f"{self.base_path}/history/{checkpoint_id}.json"
        
        posts_data = [post.dict() for post in posts]
        
        with open(history_path, 'w') as f:
            json.dump(posts_data, f, default=self._serialize_datetime)
    
    def load_post_history(self, checkpoint_id: str) -> list[Post]:
        """Load post history from disk."""
        history_path = f"{self.base_path}/history/{checkpoint_id}.json"
        
        if not os.path.exists(history_path):
            return []
            
        with open(history_path, 'r') as f:
            posts_data = json.load(f)
            
        posts_data = [self._deserialize_datetime(post) for post in posts_data]
        return [Post.parse_obj(post) for post in posts_data]
    
    def save_queues(self, state: XState, checkpoint_id: str) -> None:
        """Save post and interaction queues to disk."""
        queue_path = f"{self.base_path}/queues/{checkpoint_id}.json"
        
        queue_data = {
            'post_queue': [post.dict() for post in state.post_queue],
            'interaction_queue': {
                'pending': [post.dict() for post in state.interaction_queue.pending],
                'processing': state.interaction_queue.processing
            }
        }
        
        with open(queue_path, 'w') as f:
            json.dump(queue_data, f, default=self._serialize_datetime)
    
    def load_queues(self, checkpoint_id: str) -> tuple[list[QueuedPost], list[QueuedPost], list[str]]:
        """Load queues from disk."""
        queue_path = f"{self.base_path}/queues/{checkpoint_id}.json"
        
        if not os.path.exists(queue_path):
            return [], [], []
            
        with open(queue_path, 'r') as f:
            queue_data = json.load(f)
            
        # Deserialize post queue
        post_queue_data = [self._deserialize_datetime(post) for post in queue_data['post_queue']]
        post_queue = [QueuedPost.parse_obj(post) for post in post_queue_data]
        
        # Deserialize interaction queue
        pending_data = [self._deserialize_datetime(post) for post in queue_data['interaction_queue']['pending']]
        pending = [QueuedPost.parse_obj(post) for post in pending_data]
        processing = queue_data['interaction_queue']['processing']
        
        return post_queue, pending, processing