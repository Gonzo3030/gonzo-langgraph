from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

class AgentState(BaseModel):
    """State definition for the Gonzo agent using Pydantic."""
    messages: List[BaseMessage] = Field(default_factory=list)
    current_step: str = Field(default="initial")
    context: Dict[str, Any] = Field(default_factory=dict)
    intermediate_steps: List[Dict[str, Any]] = Field(default_factory=list)
    assistant_message: Optional[str] = None
    tools: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True