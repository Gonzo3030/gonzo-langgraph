"""Knowledge-enhanced assessment node."""

from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.language_models import BaseLLM
from langchain_core.messages import SystemMessage, HumanMessage

from ..types import GonzoState

async def enhance_assessment(state: GonzoState, llm: Optional[BaseLLM] = None) -> Dict[str, Any]:
    """Enhance assessment with knowledge base context.
    
    Args:
        state: Current state
        llm: Optional language model (for testing)
        
    Returns:
        Enhanced assessment results
    """
    try:
        if not state.patterns:
            return {"state": state, "next": "error"}
            
        # Use patterns to get relevant knowledge
        knowledge_context = {}
        for pattern in state.patterns:
            if pattern.get('type') == 'manipulation':
                knowledge_context['manipulation_tactics'] = [
                    "Media reality distortion",
                    "Corporate narrative control",
                    "Digital consciousness manipulation"
                ]
                
        # Enhance pattern analysis
        if llm:
            system_prompt = """You are Dr. Gonzo's analytical engine. 
            Enhance pattern analysis with your knowledge spanning 1974-3030."""
            
            human_prompt = f"""Original patterns: {state.patterns}
            Knowledge context: {knowledge_context}
            
            Enhance the analysis with temporal connections and dystopian implications."""
            
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ])
            
            # Update patterns with enhanced analysis
            for pattern in state.patterns:
                pattern['enhanced_analysis'] = response
                pattern['knowledge_enhanced'] = True
                
        return {"state": state, "next": "respond"}
        
    except Exception as e:
        return {"state": state, "next": "error"}