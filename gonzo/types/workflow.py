"""Workflow types for Gonzo system."""

from enum import Enum

class NextStep(str, Enum):
    """Possible next steps in workflow."""
    ASSESS = "assess"
    ANALYZE = "analyze"
    RESPOND = "respond"
    MONITOR = "monitor"
    END = "end"
    ERROR = "error"