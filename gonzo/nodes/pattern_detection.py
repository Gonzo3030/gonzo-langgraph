"""Pattern detection node for LangGraph workflow."""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from ..types import GonzoState, NextStep
from ..config import TASK_PROMPTS

async def detect_patterns(state: GonzoState, llm: Any) -> Dict[str, Any]:
    """Detect patterns in content using Gonzo's perspective.
    
    Args:
        state: Current workflow state
        llm: Language model for analysis
        
    Returns:
        Updated state and next step
    """
    try:
        if not state.analysis.entities:
            return {"state": state, "next": NextStep.ERROR}
            
        # Prepare analysis prompt
        entities_text = "\n".join(
            f"- {e.get('text', 'Unknown entity')}: {e.get('type', 'Unknown type')}" 
            for e in state.analysis.entities
        )
        
        prompt = TASK_PROMPTS["pattern_detection"].format(
            content=state.messages.current_message,
            entities=entities_text
        )
        
        # Get pattern analysis
        response = await llm.ainvoke([
            SystemMessage(content="You are Dr. Gonzo's pattern recognition system."),
            HumanMessage(content=prompt)
        ])
        
        # Add pattern to state
        state.analysis.patterns.append({
            "type": "detected_pattern",
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.8  # Base confidence, could be dynamically calculated
        })
        
        # Update state significance based on patterns
        state.analysis.significance = min(1.0, len(state.analysis.patterns) * 0.2)
        
        return {"state": state, "next": NextStep.ANALYZE}
        
    except Exception as e:
        state.messages.current_message = f"Pattern detection error: {str(e)}"
        return {"state": state, "next": NextStep.ERROR}