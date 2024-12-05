from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain.schema import BaseMessage

class BatchState(TypedDict):
    """State for batch processing."""
    events: List[Dict[str, Any]]
    batch_id: str
    timestamp: str
    similarity_score: float

class MemoryState(TypedDict):
    """State for memory management."""
    short_term: Dict[str, Dict[str, Any]]
    long_term: Dict[str, Dict[str, Any]]
    last_accessed: str

class GonzoStateDict(TypedDict):
    """Complete state dictionary for Gonzo workflow."""
    messages: List[BaseMessage]
    current_batch: Optional[BatchState]
    memory: Optional[MemoryState]
    next_step: str
    errors: Optional[List[str]]

class GonzoState(BaseModel):
    """Core state for Gonzo's analysis workflow.
    
    This follows LangGraph's state management patterns for proper integration.
    """
    state: GonzoStateDict = Field(
        default_factory=lambda: GonzoStateDict(
            messages=[],
            current_batch=None,
            memory={
                'short_term': {},
                'long_term': {},
                'last_accessed': datetime.now().isoformat()
            },
            next_step='initialize',
            errors=None
        )
    )
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the state."""
        self.state['messages'].append(message)
    
    def update_batch(self, batch: BatchState) -> None:
        """Update the current batch being processed."""
        self.state['current_batch'] = batch
    
    def save_to_memory(self, key: str, value: Any, permanent: bool = False) -> None:
        """Save data to memory, either short-term or long-term.
        
        Args:
            key: Key to store the value under
            value: Value to store
            permanent: If True, store in long-term memory
        """
        memory_type = 'long_term' if permanent else 'short_term'
        if self.state['memory'] is None:
            self.state['memory'] = {
                'short_term': {},
                'long_term': {},
                'last_accessed': datetime.now().isoformat()
            }
        
        # Store value with metadata
        self.state['memory'][memory_type][key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        self.state['memory']['last_accessed'] = datetime.now().isoformat()
    
    def get_from_memory(self, key: str, memory_type: str = 'short_term') -> Optional[Any]:
        """Retrieve data from memory.
        
        Args:
            key: Key to retrieve
            memory_type: Either 'short_term' or 'long_term'
            
        Returns:
            The stored value or None if not found
        """
        if not self.state['memory']:
            return None
            
        memory_dict = self.state['memory'][memory_type]
        if key not in memory_dict:
            return None
            
        return memory_dict[key]['value']
    
    def set_next_step(self, step: str) -> None:
        """Set the next step in the workflow."""
        self.state['next_step'] = step
    
    def add_error(self, error: str) -> None:
        """Add an error message to the state."""
        if self.state['errors'] is None:
            self.state['errors'] = []
        self.state['errors'].append(error)

    class Config:
        arbitrary_types_allowed = True