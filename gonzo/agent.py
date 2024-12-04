from typing import Dict, Any, Optional
from .graph.workflow import create_workflow
from .types import AgentState

class GonzoAgent:
    """Main Gonzo agent using LangGraph."""
    
    def __init__(self):
        self.workflow = create_workflow()
    
    def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentState:
        """Process user input through the workflow."""
        # Create initial state
        initial_state = AgentState(
            messages=[user_input],
            current_step="initial",
            context=context or {},
            intermediate_steps=[],
            assistant_message=None,
            tools={},
            errors=[]
        )
        
        # Run workflow
        return self.workflow.invoke(initial_state)