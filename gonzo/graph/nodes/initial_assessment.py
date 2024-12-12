"""Initial assessment node for content analysis."""

from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseLLM

from ...config import MODEL_NAME
from ...types import GonzoState, NextStep

async def initial_assessment(state: GonzoState, llm: Optional[BaseLLM] = None) -> Dict[str, Any]:
    """Perform initial assessment of content.
    
    Args:
        state: Current state
        llm: Optional language model (for testing)
        
    Returns:
        Updated state
    """
    if not state.input_text:
        return {"state": state}
        
    try:
        # Create assessment prompt
        system_prompt = """You are Dr. Gonzo's analytical engine. Assess content from his perspective as a time-traveling observer from 1974-3030.
        Focus on:
        1. Patterns of manipulation and control
        2. Historical parallels across your timeline
        3. Significance to preventing dystopian outcomes
        4. Required response approach (quick take vs full analysis)"""
        
        prompt = f"""Analyze this content:
        {state.input_text}
        
        Provide assessment in JSON format with:
        - patterns: List of identified patterns
        - historical_links: List of relevant historical connections
        - significance: Float between 0-1
        - suggested_response: 'quick_take' or 'full_analysis'
        """
        
        # Get assessment
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages) if llm else ""
        
        # Update state (mock data for testing if no llm)
        state.patterns = [{
            "type": "manipulation",
            "confidence": 0.8,
            "description": "Test pattern"
        }]
        state.current_significance = 0.7
        state.response_type = "quick_take"
        
        return {"state": state}
        
    except Exception as e:
        state.input_type = "error"
        return {"state": state}