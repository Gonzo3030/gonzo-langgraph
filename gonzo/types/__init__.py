"""Type definitions for Gonzo system."""

from typing import Dict, Any
from enum import Enum
from gonzo.state.base import GonzoState  # Re-export from new location

class NextStep(str, Enum):
    """Next step in workflow."""
    ANALYZE = "analyze"
    RESPOND = "respond"
    ERROR = "error"
    END = "end"

class TimeAwareEntity:
    """Base class for time-aware entities."""
    timestamp: str

__all__ = ['GonzoState', 'NextStep', 'TimeAwareEntity']