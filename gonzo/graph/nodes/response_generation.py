"""Response generation node."""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from ...types import GonzoState, NextStep
from ...config import MODEL_CONFIG, SYSTEM_PROMPT

async def generate_response(state: GonzoState) -> Dict[str, Any]:
    """Generate appropriate response.
    
    Args:
        state: Current state
        
    Returns:
        Next step in workflow
    """
    try:
        # Determine response type based on analysis
        if state.analysis.significance > 0.8:
            state.response.response_type = "thread_analysis"
        elif state.analysis.significance > 0.6:
            state.response.response_type = "historical_bridge"
        else:
            state.response.response_type = "quick_take"
            
        # Add response to queue
        response_data = {
            "type": state.response.response_type,
            "patterns": state.analysis.patterns,
            "significance": state.analysis.significance,
            "timestamp": datetime.now().isoformat()
        }
        
        state.response.queued_responses.append(response_data)
        
        return {"state": state, "next": NextStep.END}
        
    except Exception as e:
        return {"state": state, "next": NextStep.ERROR}