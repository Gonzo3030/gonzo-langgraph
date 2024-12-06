from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Represents a message in the system."""
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class GonzoState(BaseModel):
    """State object for Gonzo workflow."""
    messages: List[Message] = Field(default_factory=list)
    memory: Dict[str, Any] = Field(default_factory=dict)
    next_step: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    def add_message(self, message: Message) -> None:
        """Add a message to the state."""
        self.messages.append(message)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def set_next_step(self, step: str) -> None:
        """Set the next step in the workflow."""
        self.next_step = step

    def save_to_memory(self, key: str, value: Any, permanent: bool = False) -> None:
        """Save a value to memory."""
        if permanent:
            if "long_term" not in self.memory:
                self.memory["long_term"] = {}
            self.memory["long_term"][key] = value
        else:
            if "short_term" not in self.memory:
                self.memory["short_term"] = {}
            self.memory["short_term"][key] = value

    def get_from_memory(self, key: str, memory_type: str = "short_term") -> Optional[Any]:
        """Retrieve a value from memory."""
        if memory_type in self.memory and key in self.memory[memory_type]:
            return self.memory[memory_type][key]
        return None

def create_initial_state() -> GonzoState:
    """Create an initial state for the workflow."""
    return GonzoState()