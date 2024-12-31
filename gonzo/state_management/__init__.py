"""State management for Gonzo MVP."""
from enum import Enum
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from operator import add
from pydantic import BaseModel
from datetime import datetime

class WorkflowStage(str, Enum):
    """Basic workflow stages"""
    MONITORING = 'monitoring'
    ANALYSIS = 'analysis'
    REPORTING = 'reporting'
    PUBLISHING = 'publishing'
    ERROR = 'error'
    COMPLETE = 'complete'

class Event(BaseModel):
    """Represents a monitored event/development"""
    timestamp: datetime
    title: str
    content: str
    source: str
    url: Optional[str] = None

class Pattern(BaseModel):
    """Represents an identified pattern between events"""
    events: List[Event]
    description: str
    significance: float  # 0-1 scale of pattern significance
    implications: List[str]

class Insight(BaseModel):
    """Represents Gonzo's analysis and commentary"""
    pattern: Pattern
    commentary: str
    warnings: List[str]
    timestamp: datetime

class QueuedPost(BaseModel):
    """Represents a post scheduled for publishing"""
    insight: Insight
    scheduled_time: datetime
    status: str  # 'queued', 'published', 'failed'
    error: Optional[str] = None

class GonzoState(BaseModel):
    """Simplified state for Gonzo MVP"""
    events: List[Event] = []
    patterns: List[Pattern] = []
    insights: List[Insight] = []
    queued_posts: List[QueuedPost] = []
    published_posts: List[Dict] = []
    ready_posts: List[Dict] = []
    remaining_posts: List[Dict] = []
    current_stage: WorkflowStage = WorkflowStage.MONITORING
    errors: List[str] = []

class GonzoGraphState(TypedDict):
    """State schema for LangGraph"""
    events: Annotated[list, add]            # Use add for list concatenation
    patterns: Annotated[list, add]          # Use add for list concatenation
    insights: Annotated[list, add]          # Use add for list concatenation
    queued_posts: Annotated[list, add]      # Posts waiting to be published
    published_posts: Annotated[list, add]   # Successfully published posts
    ready_posts: Annotated[list, add]       # Posts ready for immediate publishing
    remaining_posts: Annotated[list, add]   # Posts still in queue
    current_stage: str                      # Simple string field
    errors: Annotated[list, add]            # Use add for list concatenation

def create_initial_state() -> GonzoState:
    """Create initial state for Gonzo"""
    return GonzoState()

def create_empty_graph_state() -> GonzoGraphState:
    """Create empty graph state for LangGraph"""
    return GonzoGraphState(
        events=[],
        patterns=[],
        insights=[],
        queued_posts=[],
        published_posts=[],
        ready_posts=[],
        remaining_posts=[],
        current_stage=WorkflowStage.MONITORING.value,
        errors=[]
    )