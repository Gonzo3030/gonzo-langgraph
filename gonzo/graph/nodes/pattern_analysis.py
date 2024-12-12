"""Pattern analysis node."""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from ...types import GonzoState, NextStep
from ...config import MODEL_CONFIG

async def analyze_patterns(state: GonzoState) -> Dict[str, Any]:
    """Analyze patterns in the content.
    
    Args:
        state: Current state
        
    Returns:
        Next step in workflow
    """
    try:
        if not state.analysis.patterns:
            return {"state": state, "next": NextStep.ERROR}
            
        # Update significance based on patterns
        pattern_significance = sum(
            pattern.get('confidence', 0.5) 
            for pattern in state.analysis.patterns
        ) / len(state.analysis.patterns)
        
        state.analysis.significance = pattern_significance
        
        # Determine if we need to generate a response
        if pattern_significance > 0.5:
            return {"state": state, "next": NextStep.RESPOND}
        else:
            return {"state": state, "next": NextStep.END}
            
    except Exception as e:
        return {"state": state, "next": NextStep.ERROR}