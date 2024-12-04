from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class GonzoState(TypedDict):
    """Type definition for Gonzo agent state"""
    messages: List[BaseMessage]  # Conversation history
    current_step: str  # Current step in the workflow
    context: Dict[str, Any]  # Context information
    intermediate_steps: List[Dict[str, Any]]  # Track intermediate steps
    assistant_message: Optional[str]  # Final response message
    tools: Dict[str, Any]  # Available tools
    errors: List[str]  # Any errors encountered