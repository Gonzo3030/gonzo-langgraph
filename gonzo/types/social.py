from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

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