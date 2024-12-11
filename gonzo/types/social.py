from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class PostMetrics(BaseModel):
    """Metrics for a social media post."""
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    views: int = 0

class Post(BaseModel):
    """Represents a social media post."""
    id: str
    platform: str
    content: str
    created_at: datetime
    metrics: Optional[PostMetrics] = None
    reply_to_id: Optional[str] = None
    author_id: Optional[str] = None

class QueuedPost(BaseModel):
    """Represents a post waiting to be published."""
    content: str
    priority: int = 1
    scheduled_time: Optional[datetime] = None
    reply_to_id: Optional[str] = None
    context: Dict[str, Any] = {}

class PostHistory(BaseModel):
    """Tracks history of posts and interactions."""
    posts: List[Post] = []
    last_interaction_time: Optional[datetime] = None
    interaction_counts: Dict[str, int] = {}
    
    def add_post(self, post: Post):
        """Add a post to history with timestamp."""
        self.posts.append(post)
        self.last_interaction_time = datetime.now()
        
    def get_recent_posts(self, limit: int = 10) -> List[Post]:
        """Get most recent posts."""
        return sorted(self.posts, key=lambda x: x.created_at, reverse=True)[:limit]

class InteractionQueue(BaseModel):
    """Manages pending interactions/replies."""
    pending: List[QueuedPost] = []
    processing: List[str] = []  # IDs of posts being processed
    
    def add_interaction(self, post: QueuedPost):
        """Add new interaction to queue."""
        self.pending.append(post)
        
    def get_next(self) -> Optional[QueuedPost]:
        """Get next interaction to process."""
        if not self.pending:
            return None
        return sorted(self.pending, key=lambda x: x.priority, reverse=True)[0]
