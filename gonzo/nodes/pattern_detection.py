"""Pattern detection node for LangGraph workflow."""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from ..types import GonzoState
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
        
        # Extract content from AIMessage
        response_text = response.content
        
        # Add pattern to state
        pattern = {
            "type": "manipulation" if "manipulation" in response_text.lower() else "detected_pattern",
            "content": response_text,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.9 if "manipulation" in response_text.lower() else 0.8
        }
        
        # Update state directly
        state.analysis.patterns.append(pattern)
        state.analysis.update_significance()
        state.timestamp = datetime.now()
        
        # Return updates
        return {
            "analysis": state.analysis,
            "timestamp": state.timestamp,
            "next": "assess"
        }
        
    except Exception as e:
        # Update error state
        state.add_error(f"Pattern detection error: {str(e)}")
        state.timestamp = datetime.now()
        return {
            "memory": state.memory,
            "timestamp": state.timestamp,
            "next": "error"
        }