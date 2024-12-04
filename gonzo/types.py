from typing import TypedDict, List, Annotated, Dict, Any
from langchain_core.messages import BaseMessage
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
def create_initial_state(input_message: str) -> GonzoState:
    """Create initial state for Gonzo agent."""
    return GonzoState(
        messages=[input_message], 
        context={},
        steps=[],
        timestamp=datetime.now().isoformat(),
        category="",
        response=""
    )