"""Initial assessment node."""

from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.language_models import BaseLLM
from langchain_core.messages import SystemMessage, HumanMessage

from ...types import GonzoState, NextStep
from ...config import MODEL_CONFIG, SYSTEM_PROMPT

async def initial_assessment(state: GonzoState) -> Dict[str, Any]:
    """Perform initial assessment of content.
    
    Args:
        state: Current state
        
    Returns:
        Next step in workflow
    """
    try:
        if not state.messages.current_message:
            return {"state": state, "next": NextStep.ERROR}
            
        # Analyze current message
        state.analysis.patterns.append({
            "type": "initial",
            "confidence": 0.7,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"state": state, "next": NextStep.ANALYZE}
        
    except Exception as e:
        return {"state": state, "next": NextStep.ERROR}