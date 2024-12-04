from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .graph.workflow import create_workflow
from .types import MessagesState
from .config import SYSTEM_PROMPT

class GonzoAgent:
    """Main Gonzo agent using LangGraph."""
    
    def __init__(self):
        self.workflow = create_workflow()
    
    def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> MessagesState:
        """Process user input through the workflow."""
        # Create initial state
        initial_state = MessagesState(
            messages=[
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_input)
            ],
            current_step="initial",
            context=context or {},
            intermediate_steps=[],
            assistant_message=None,
            tools={},
            errors=[]
        )
        
        # Run workflow
        return self.workflow.invoke(initial_state)