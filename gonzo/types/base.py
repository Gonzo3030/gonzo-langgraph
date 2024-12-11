from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from langchain_core.messages import BaseMessage

class NextStep(str, Enum):
    """Possible next steps in the workflow."""
    MONITOR = "monitor"
    RAG = "rag"
    ASSESSMENT = "assessment"
    QUEUE = "queue"
    END = "end"

class GonzoState(BaseModel):
    """State container for Gonzo workflow."""
    messages: List[BaseMessage] = []
    next_step: Optional[NextStep] = None
    data: Dict[str, Any] = {}
    error_log: List[Dict[str, Any]] = []
    step_log: List[Dict[str, Any]] = []
    
    def add_error(self, error: str, context: Dict[str, Any] = {}):
        """Log an error with timestamp."""
        self.error_log.append({
            'timestamp': datetime.now().isoformat(),
            'error': error,
            'context': context
        })
    
    def log_step(self, step: str, data: Dict[str, Any] = {}):
        """Log a workflow step."""
        self.step_log.append({
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'data': data
        })

def create_initial_state(messages: List[BaseMessage]) -> GonzoState:
    """Create initial state for workflow."""
    return GonzoState(
        messages=messages,
        next_step=NextStep.MONITOR
    )