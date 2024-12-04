from typing import TypedDict, List, Annotated, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage
from datetime import datetime

# Core state type for Gonzo agent
class GonzoState(TypedDict):
    """Central state definition for Gonzo agent."""
    messages: List[BaseMessage]  # Conversation history
    context: Dict[str, Any]     # Current context information
    steps: List[Dict[str, Any]] # Track agent steps and progress
    timestamp: str              # Current operation timestamp
    category: str               # Current category (crypto/narrative/general)
    response: str               # Final response to user

# Channel type for state updates
Channel = Annotated[GonzoState, "channel"]

# Helper function for creating initial state
def create_initial_state(input_message: str | BaseMessage) -> GonzoState:
    """Create initial state for Gonzo agent.
    
    Args:
        input_message: Either a string or BaseMessage object containing user input
        
    Returns:
        GonzoState: Initial state for the agent
    """
    # Convert string to HumanMessage if needed
    if isinstance(input_message, str):
        message = HumanMessage(content=input_message)
    else:
        message = input_message
        
    return GonzoState(
        messages=[message],
        context={},
        steps=[],
        timestamp=datetime.now().isoformat(),
        category="",
        response=""
    )

def update_state(state: GonzoState, updates: Dict[str, Any]) -> GonzoState:
    """Apply updates to state copy.
    
    Args:
        state: Current state
        updates: Dictionary of updates to apply
        
    Returns:
        GonzoState: New state with updates applied
    """
    new_state = state.copy()
    for key, value in updates.items():
        if key in new_state:
            if isinstance(value, list) and isinstance(new_state[key], list):
                new_state[key] = new_state[key] + value
            elif isinstance(value, dict) and isinstance(new_state[key], dict):
                new_state[key] = {**new_state[key], **value}
            else:
                new_state[key] = value
    return new_state