from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from enum import Enum, auto
from pydantic import BaseModel, Field

class EntityType(str, Enum):
    """Types of entities that can be extracted."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    CONCEPT = "CONCEPT"
    CLAIM = "CLAIM"
    NARRATIVE = "NARRATIVE"
    EVENT = "EVENT"
    LOCATION = "LOCATION"
    DATE = "DATE"
    UNKNOWN = "UNKNOWN"

class NextStep(str, Enum):
    """Next step in the workflow."""
    NARRATIVE = "narrative"
    CRYPTO = "crypto"
    GENERAL = "general"
    ERROR = "error"
    END = "end"

class Property(BaseModel):
    """Represents a property with temporal metadata."""
    key: str
    value: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TimeAwareEntity(BaseModel):
    """Base class for entities with temporal awareness."""
    type: str
    id: UUID
    properties: Dict[str, Property]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime
    valid_to: Optional[datetime] = None
    previous_versions: List[Any] = Field(default_factory=list)

class Relationship(BaseModel):
    """Represents a relationship between entities."""
    type: str
    id: UUID
    source_id: UUID
    target_id: UUID
    properties: Dict[str, Property] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    causal_strength: Optional[float] = None
    temporal_ordering: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Message(BaseModel):
    """Represents a message in the system."""
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class MessagesState(BaseModel):
    """State for managing message history."""
    messages: List[Message] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)

class GonzoState(BaseModel):
    """State object for Gonzo workflow."""
    messages: List[Message] = Field(default_factory=list)
    memory: Dict[str, Any] = Field(default_factory=dict)
    next_step: Optional[NextStep] = None
    errors: List[str] = Field(default_factory=list)

    def add_message(self, message: Message) -> None:
        """Add a message to the state."""
        self.messages.append(message)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def set_next_step(self, step: NextStep) -> None:
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

def update_state(state: GonzoState, updates: Dict[str, Any]) -> GonzoState:
    """Update the state with new values.
    
    Args:
        state: Current state
        updates: Dictionary of updates to apply
        
    Returns:
        Updated state
    """
    for key, value in updates.items():
        if hasattr(state, key):
            setattr(state, key, value)
    return state