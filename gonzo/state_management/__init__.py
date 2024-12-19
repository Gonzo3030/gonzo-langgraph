"""State management for Gonzo system."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class WorkflowStage(str, Enum):
    """Workflow stages for Gonzo's operation"""
    INITIALIZATION = "initialization"
    MARKET_MONITORING = "market_monitoring"
    SOCIAL_MONITORING = "social_monitoring"
    NEWS_MONITORING = "news_monitoring"
    PATTERN_ANALYSIS = "pattern_analysis"
    NARRATIVE_GENERATION = "narrative_generation"
    RESPONSE_POSTING = "response_posting"
    ERROR_RECOVERY = "error_recovery"
    CYCLE_COMPLETE = "cycle_complete"
    SHUTDOWN = "shutdown"