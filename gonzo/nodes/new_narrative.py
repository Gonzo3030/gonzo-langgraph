"""Narrative analysis node."""

from typing import Dict, Any
from datetime import datetime
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseLLM
from ..config import MODEL_NAME
from ..types import GonzoState

logger = logging.getLogger(__name__)

async def analyze_narrative(state: GonzoState, llm: BaseLLM) -> Dict[str, Any]:
    """Analyze narrative content."""
    try:
        if not state.input_text:
            return {"state": state, "next": "error"}
        
        # Create narrative analysis prompt
        system_prompt = """You are Dr. Gonzo analyzing a narrative for patterns of manipulation.
        Draw from your experience from 1974-3030 to identify control mechanisms and dystopian parallels."""
        
        analysis_prompt = f"""Analyze this content for narrative manipulation tactics:
        
        {state.input_text}
        
        Focus on:
        1. Control mechanisms
        2. Reality distortion methods
        3. Historical parallels
        4. Connection to dystopian outcomes"""
        
        # Get analysis
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Update state
        state.patterns.append({
            "type": "narrative",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"state": state, "next": "respond"}
        
    except Exception as e:
        logger.error(f"Narrative analysis error: {str(e)}")
        return {"state": state, "next": "error"}