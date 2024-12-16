"""State update utilities."""

from typing import Dict, Any
from ..types import GonzoState

def update_state(state: GonzoState, updates: Dict[str, Any]) -> GonzoState:
    """Update state with new values.
    
    Args:
        state: Current state object
        updates: Dictionary of updates to apply
        
    Returns:
        Updated state
    """
    for key, value in updates.items():
        if hasattr(state, key):
            setattr(state, key, value)
    return state