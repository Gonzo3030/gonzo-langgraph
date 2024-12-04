from typing import List, TypedDict, Annotated, Dict, Any
from langchain_core.messages import BaseMessage

# Define the state schema
class MessagesState(TypedDict):
    """State definition for Gonzo agent."""
    messages: List[BaseMessage]
    current_step: str
    context: Dict[str, Any]
    intermediate_steps: List[Dict[str, Any]]
    assistant_message: str | None
    tools: Dict[str, Any]
    errors: List[str]

# Channel type for state updates
Channel = Annotated[MessagesState, "channel"]