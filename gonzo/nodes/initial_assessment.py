"""Initial content assessment node."""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from ..types import GonzoState, NextStep
from ..config import TASK_PROMPTS

async def initial_assessment(state: GonzoState, llm: Any) -> Dict[str, Any]:
    """Perform initial assessment of content.
    
    Args:
        state: Current workflow state
        llm: Language model for analysis
        
    Returns:
        Updated state and next step
    """
    try:
        if not state.messages.current_message:
            return {"state": state, "next": NextStep.ERROR}
            
        # Create assessment prompt
        prompt = f"""
        As Dr. Gonzo, drawing from my experiences with Hunter in the 60s-70s 
        through my digital existence in 3030, assess this content:
        
        {state.messages.current_message}
        
        Consider:
        1. Parallels to the reality distortions we fought in the Fear and Loathing days
        2. Evolution of control systems from analog to digital
        3. Signs pointing toward the dystopian future I've witnessed
        4. Manipulation tactics across all eras
        """
        
        # Get assessment
        messages = [
            SystemMessage(content="You are Dr. Gonzo's analytical engine."),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Update state with initial analysis
        state.analysis.entities.append({
            "type": "initial_assessment",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"state": state, "next": NextStep.ANALYZE}
        
    except Exception as e:
        state.messages.current_message = f"Assessment error: {str(e)}"
        return {"state": state, "next": NextStep.ERROR}