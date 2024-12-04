from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from .graph.workflow import create_workflow
from .types import GonzoState, create_initial_state
from .config import SYSTEM_PROMPT

class GonzoAgent:
    """Main Gonzo agent using LangGraph."""
    
    def __init__(self):
        self.workflow = create_workflow()
    
    def run(self, user_input: str) -> GonzoState:
        """Process user input through the workflow."""
        # Create messages list with system prompt
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input)
        ]
        
        # Create initial state
        initial_state = create_initial_state(messages)
        
        # Run workflow
        return self.workflow.invoke(initial_state)