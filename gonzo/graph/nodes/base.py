from typing import Dict, Any, Optional, TypeVar, List
from datetime import datetime
from langchain_core.messages import BaseMessage
from ...types.base import GonzoState

StateType = TypeVar("StateType")

def update_state(state: GonzoState, updates: Dict[str, Any]) -> GonzoState:
    """Update state with new values."""
    for key, value in updates.items():
        if hasattr(state, key):
            setattr(state, key, value)
    return state

def log_step(state: GonzoState, step_name: str, result: Any) -> None:
    """Log a workflow step."""
    if not hasattr(state, 'steps'):
        setattr(state, 'steps', [])
    
    if not isinstance(state.steps, list):
        state.steps = []
    
    state.steps.append({
        'step': step_name,
        'result': result,
        'timestamp': datetime.now().isoformat()
    })

def get_latest_message(state: GonzoState) -> Optional[BaseMessage]:
    """Get the latest message from state."""
    if state.messages:
        return state.messages[-1]
    return None

def add_to_messages(state: GonzoState, message: BaseMessage) -> None:
    """Add a message to state's message history."""
    if not hasattr(state, 'messages'):
        state.messages = []
    state.messages.append(message)