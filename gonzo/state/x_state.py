"""State management for X integration."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MonitoringState(BaseModel):
    """State for content monitoring."""
    last_check: datetime = Field(default_factory=datetime.now)
    monitored_keywords: List[str] = Field(default_factory=list)
    monitored_accounts: List[str] = Field(default_factory=list)
    active_threads: Dict[str, List[str]] = Field(default_factory=dict)

class XState(BaseModel):
    """State for X interactions."""
    monitoring: MonitoringState = Field(default_factory=MonitoringState)
    pending_responses: List[Dict[str, Any]] = Field(default_factory=list)
    active_conversations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    rate_limit_info: Dict[str, Any] = Field(default_factory=dict)
    
    def update_monitoring(self, keywords: Optional[List[str]] = None, accounts: Optional[List[str]] = None):
        """Update monitoring configuration."""
        if keywords:
            self.monitoring.monitored_keywords = keywords
        if accounts:
            self.monitoring.monitored_accounts = accounts
            
    def add_pending_response(self, response_data: Dict[str, Any]):
        """Add response to pending queue."""
        self.pending_responses.append(response_data)
        
    def start_conversation(self, thread_id: str, conversation_data: Dict[str, Any]):
        """Start tracking a new conversation."""
        self.active_conversations[thread_id] = conversation_data
        
    def update_rate_limits(self, limits: Dict[str, Any]):
        """Update rate limit information."""
        self.rate_limit_info = limits