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
        # Initialize entities if None
        if state.analysis.entities is None:
            state.analysis.entities = []

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
            SystemMessage(content="You are Dr. Gonzo's pattern recognition system. "
                                "Pay special attention to manipulation patterns, distortion techniques, "
                                "and coordinated narrative control."),
            HumanMessage(content=prompt)
        ])
        
        # Add pattern to state
        pattern = {
            "type": "manipulation" if "manipulation" in response.lower() else "detected_pattern",
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.9 if "manipulation" in response.lower() else 0.8
        }
        
        # Initialize patterns list if None
        if state.analysis.patterns is None:
            state.analysis.patterns = []
            
        state.analysis.patterns.append(pattern)
        
        # Use state's significance calculation
        state.update_analysis()
        
        return {"state": state, "next": NextStep.ANALYZE}
        
    except Exception as e:
        state.add_error(f"Pattern detection error: {str(e)}")
        return {"state": state, "next": NextStep.ERROR}