"""State persistence for Gonzo."""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from langchain.storage import LocalFileStore

logger = logging.getLogger(__name__)

class GonzoStateStore:
    """Handles persistent state storage for Gonzo workflows."""
    
    def __init__(self, base_path: str = "./state"):
        self.store = LocalFileStore(Path(base_path))
        self.queue_key = "post_queue"
        self.state_key = "current_state"
    
    def _serialize_datetime(self, obj: Any) -> Any:
        """Handle datetime serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def _deserialize_datetime(self, obj: Any) -> Any:
        """Handle datetime deserialization."""
        if isinstance(obj, str):
            try:
                return datetime.fromisoformat(obj)
            except ValueError:
                pass
        return obj
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save full workflow state."""
        try:
            # Serialize with datetime handling
            serialized = json.dumps(state, default=self._serialize_datetime)
            self.store.mset([(self.state_key, serialized)])
            logger.debug(f"Saved state with {len(state.get('queued_posts', []))} queued posts")
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load full workflow state."""
        try:
            serialized = self.store.mget([self.state_key])[0]
            if serialized:
                state = json.loads(serialized)
                # Deserialize datetime objects
                if 'queued_posts' in state:
                    for post in state['queued_posts']:
                        if 'scheduled_time' in post:
                            post['scheduled_time'] = self._deserialize_datetime(post['scheduled_time'])
                logger.debug(f"Loaded state with {len(state.get('queued_posts', []))} queued posts")
                return state
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}")
        return None
    
    def update_queue(self, posts: list) -> None:
        """Update just the post queue."""
        try:
            serialized = json.dumps(posts, default=self._serialize_datetime)
            self.store.mset([(self.queue_key, serialized)])
            logger.debug(f"Updated queue with {len(posts)} posts")
        except Exception as e:
            logger.error(f"Error updating queue: {str(e)}")
    
    def get_queue(self) -> list:
        """Get just the post queue."""
        try:
            serialized = self.store.mget([self.queue_key])[0]
            if serialized:
                posts = json.loads(serialized)
                # Deserialize datetime objects
                for post in posts:
                    if 'scheduled_time' in post:
                        post['scheduled_time'] = self._deserialize_datetime(post['scheduled_time'])
                logger.debug(f"Retrieved queue with {len(posts)} posts")
                return posts
        except Exception as e:
            logger.error(f"Error getting queue: {str(e)}")
        return []
