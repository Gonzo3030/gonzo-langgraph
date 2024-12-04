from typing import List, Dict, Any
from langchain_core.messages import BaseMessage

class WindowMemory:
    """Maintains a sliding window of recent conversation history."""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.messages: List[BaseMessage] = []
        
    def add_message(self, message: BaseMessage):
        """Add a new message to the window."""
        self.messages.append(message)
        if len(self.messages) > self.window_size:
            self.messages.pop(0)
    
    def get_messages(self) -> List[BaseMessage]:
        """Get all messages in the current window."""
        return self.messages
    
    def clear(self):
        """Clear all messages."""
        self.messages = []