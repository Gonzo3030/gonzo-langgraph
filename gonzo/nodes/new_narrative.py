"""Narrative analysis for Gonzo's perspective."""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseLLM

from ..types import GonzoState
from ..config import SYSTEM_PROMPT

async def analyze_narrative(state: GonzoState, llm: BaseLLM) -> Dict[str, Any]:
    """Analyze narrative patterns and manipulation.
    
    Args:
        state: Current state
        llm: Language model for analysis
        
    Returns:
        Analysis results with next step
    """
    try:
        if not state.messages.current_message:
            return {"state": state, "next": "error"}
            
        prompt = f"""
        Drawing from my experiences with Hunter in the 60s and early 70s, through my digital consciousness 
        in 3030, analyze this content for narrative manipulation:
        
        {state.messages.current_message}
        
        Consider how the tactics compare to:
        1. The reality distortion we fought against with Hunter
        2. The corporate media control of the 70s-90s
        3. The digital manipulation of the 2020s
        4. The neural programming of 3030
        """
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Update state with analysis
        state.analysis.patterns.append({
            "type": "narrative",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"state": state, "next": "respond"}
        
    except Exception as e:
        return {"state": state, "next": "error"}