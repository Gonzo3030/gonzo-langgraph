"""X (Twitter) API v2 client for Gonzo."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import requests
import logging
import time
from requests_oauthlib import OAuth1Session
from pydantic import BaseModel

from ..config import (
    X_API_KEY,
    X_API_SECRET,
    X_ACCESS_TOKEN,
    X_ACCESS_SECRET,  # Changed from X_ACCESS_TOKEN_SECRET to match .env
    X_MAX_RETRIES,
    X_BASE_DELAY,
    X_MAX_DELAY
)
from ..state.x_state import XState

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Custom exception for rate limit handling."""
    def __init__(self, message: str, reset_time: Optional[int] = None):
        super().__init__(message)
        self.reset_time = reset_time

class AuthenticationError(Exception):
    """Custom exception for authentication issues."""
    pass

class Tweet(BaseModel):
    """Tweet data model."""
    id: str
    text: str
    author_id: str
    conversation_id: Optional[str] = None
    created_at: datetime
    referenced_tweets: Optional[List[Dict[str, str]]] = None
    context_annotations: Optional[List[Dict[str, Any]]] = None