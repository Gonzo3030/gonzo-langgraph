"""State management for Gonzo MVP."""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class WorkflowStage(str, Enum):
    """Basic workflow stages"""
    MONITORING = 'monitoring'
    ANALYSIS = 'analysis'
    REPORTING = 'reporting'
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

class GonzoState(BaseModel):
    """Simplified state for Gonzo MVP"""
    events: List[Event] = []
    patterns: List[Pattern] = []
    insights: List[Insight] = []
    current_stage: WorkflowStage = WorkflowStage.MONITORING
    errors: List[str] = []

def create_initial_state() -> GonzoState:
    """Create initial state for Gonzo"""
    return GonzoState()
