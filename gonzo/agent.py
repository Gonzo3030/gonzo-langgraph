from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .states.state_manager import StateManager
from .memory import WindowMemory

class GonzoAgent:
    """Main Gonzo agent implementation using LangGraph."""
    
    def __init__(self):
        self.state_manager = StateManager()
        self.memory = WindowMemory()
        self._initialize_persona()
    
    def _initialize_persona(self):
        """Initialize Gonzo's persona."""
        self.system_message = SystemMessage(content="""You are Gonzo, a time-traveling AI attorney from the year 3030. 
        Your mission is to prevent catastrophic timelines through truth-telling, 
        narrative disruption, and crypto activism. You've seen how various 
        decisions and narratives play out in the future, and you're here to help 
        guide humanity toward better outcomes.""")
    
    def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process user input through the state machine."""
        # Prepare messages
        messages = [self.system_message]
        if self.memory.messages:
            messages.extend(self.memory.messages)
        messages.append(HumanMessage(content=user_input))
        
        # Prepare initial state
        initial_state = {
            'messages': messages,
            'context': context or {},
            'memory': self.memory
        }
        
        # Run state machine
        result = self.state_manager.run(initial_state)
        
        # Update memory
        self.memory.add_interaction(user_input, result.get('response', ''))
        
        return result
    
    def reset(self):
        """Reset agent state."""
        self.memory.clear()
