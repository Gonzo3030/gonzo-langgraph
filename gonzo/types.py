from typing import TypedDict, List, Annotated, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage
from datetime import datetime

class GonzoState(TypedDict, total=False):
    """Central state definition for Gonzo agent.
    
    Using total=False to make all fields optional.
    """
    # Core fields
    messages: List[BaseMessage]  # Conversation history
    context: Dict[str, Any]     # Current context information
    steps: List[str]           # Track agent steps and progress
    timestamp: str              # Current operation timestamp
    category: str               # Current category (market/narrative/causality)
    response: str               # Final response to user
    
    # Analysis flags and results
    market_analysis_completed: bool
    market_analysis_timestamp: str
    narrative_analysis_completed: bool
    narrative_analysis_timestamp: str
    causality_analysis_completed: bool
    causality_analysis_timestamp: str
    
    # Analysis requirements
    requires_market_analysis: bool
    requires_narrative_analysis: bool
    requires_causality_analysis: bool

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
    new_state = dict(state)
    for key, value in updates.items():
        if isinstance(value, list) and key in new_state and isinstance(new_state[key], list):
            new_state[key] = new_state[key] + value
        elif isinstance(value, dict) and key in new_state and isinstance(new_state[key], dict):
            new_state[key].update(value)
        else:
            new_state[key] = value
    return new_state