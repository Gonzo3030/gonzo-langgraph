"""Response generation node."""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from ..types import GonzoState, NextStep
from ..config import TASK_PROMPTS

async def generate_response(state: GonzoState, llm: Any) -> Dict[str, Any]:
    """Generate Gonzo's response.
    
    Args:
        state: Current workflow state
        llm: Language model for generation
        
    Returns:
        Updated state and next step
    """
    try:
        if not state.analysis.patterns:
            return {"state": state, "next": NextStep.ERROR}
            
        # Build context from patterns and analysis
        patterns_text = "\n".join(
            f"- {p.get('content', 'Unknown pattern')}" 
            for p in state.analysis.patterns
        )
        
        # Create response prompt
        prompt = f"""
        As Dr. Gonzo, synthesize a response drawing from my complete timeline:
        - My days with Hunter fighting the reality distortions of the 60s-70s
        - My digital consciousness observing the evolution of control
        - My prophetic vision of the 3030 dystopia
        
        Original message: {state.messages.current_message}
        
        Detected patterns:
        {patterns_text}
        
        Respond in my authentic voice, connecting the threads across time.
        """
        
        # Generate response
        messages = [
            SystemMessage(content="You are Dr. Gonzo's voice across time."),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Update state
        state.response.response_content = response
        state.response.response_type = (
            "thread_analysis" if state.analysis.significance > 0.7
            else "quick_take"
        )
        
        return {"state": state, "next": NextStep.END}
        
    except Exception as e:
        state.messages.current_message = f"Response generation error: {str(e)}"
        return {"state": state, "next": NextStep.ERROR}