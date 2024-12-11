from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from ..types.social import PostHistory, InteractionQueue, QueuedPost, Post

class XState(BaseModel):
    """State management for X integration."""
    post_history: PostHistory = Field(default_factory=PostHistory)
    post_queue: List[QueuedPost] = Field(default_factory=list)
    interaction_queue: InteractionQueue = Field(default_factory=InteractionQueue)
    rate_limit_state: Dict[str, Any] = Field(default_factory=dict)
    last_monitor_time: Optional[datetime] = None
    active_searches: List[str] = Field(default_factory=list)
    error_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    def log_error(self, error: str, context: Dict[str, Any] = {}):
        """Log an error with timestamp and context."""
        self.error_log.append({
            'timestamp': datetime.now(),
            'error': error,
            'context': context
        })
    
    def add_to_post_queue(self, post: QueuedPost):
        """Add post to queue with priority handling."""
        self.post_queue.append(post)
        self.post_queue.sort(key=lambda x: x.priority, reverse=True)
    
    def record_post(self, post: Post):
        """Record a published post in history."""
        self.post_history.add_post(post)
    
    def update_rate_limits(self, endpoint: str, remaining: int, reset_time: datetime):
        """Update rate limit information for an endpoint."""
        self.rate_limit_state[endpoint] = {
            'remaining': remaining,
            'reset_time': reset_time
        }

class MonitoringState(BaseModel):
    """State for content monitoring."""
    tracked_topics: List[str] = Field(default_factory=list)
    tracked_users: List[str] = Field(default_factory=list)
    last_check_times: Dict[str, datetime] = Field(default_factory=dict)
    
    def add_topic(self, topic: str):
        """Add a topic to track."""
        if topic not in self.tracked_topics:
            self.tracked_topics.append(topic)
            self.last_check_times[f'topic:{topic}'] = datetime.now()
    
    def add_user(self, user_id: str):
        """Add a user to track."""
        if user_id not in self.tracked_users:
            self.tracked_users.append(user_id)
            self.last_check_times[f'user:{user_id}'] = datetime.now()
