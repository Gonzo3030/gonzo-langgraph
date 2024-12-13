"""Integration tests for narrative analysis flow."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from gonzo.state import GonzoState
from gonzo.nodes.new_narrative import analyze_narrative
from gonzo.nodes.knowledge_enhanced_narrative import enhance_narrative

@pytest.mark.asyncio
async def test_full_narrative_flow(mock_llm):
    """Test the complete narrative analysis flow with knowledge enhancement."""
    # Create initial state with test message
    state = GonzoState()
    state.messages.current_message = """
    The crypto markets are showing classic signs of manipulation again. 
    Bitcoin's sudden pump coincides perfectly with the SEC's latest FUD campaign. 
    Meanwhile, the mainstream media narrative shifts like a weathervane in a tornado - 
    first it's 'crypto is dead', then suddenly it's 'institutional adoption is here'. 
    The same old players are pulling the same old strings, just with fancier algorithms 
    and slicker PR campaigns. You can smell the sulfur of market manipulation from a mile away.
    """
    
    # Run initial narrative analysis
    narrative_result = await analyze_narrative(state, mock_llm)
    
    # Verify initial analysis
    assert narrative_result["next"] == "respond"
    assert len(state.analysis.patterns) > 0
    assert any(p["type"] == "narrative" for p in state.analysis.patterns)
    
    # Run knowledge enhancement
    knowledge_result = await enhance_narrative(state)
    assert knowledge_result["next"] is not None
    
    # Add a follow-up narrative after some time
    state.messages.current_message = """
    The aftermath of yesterday's crypto pump is exactly what you'd expect 
    in this rigged casino. The same institutional players who were spreading 
    FUD last week are now touting their 'strategic blockchain investments'. 
    The pattern is so obvious it hurts - create fear, accumulate in the dark, 
    pump in the light. The more things change, the more they stay the same in 
    this digital Wild West.
    """
    
    # Run second analysis
    narrative_result2 = await analyze_narrative(state, mock_llm)
    assert narrative_result2["next"] == "respond"
    
    # Verify pattern accumulation
    assert len(state.analysis.patterns) > 1
    narrative_patterns = [p for p in state.analysis.patterns if p["type"] == "narrative"]
    assert len(narrative_patterns) >= 2
    
    # Run second knowledge enhancement
    knowledge_result2 = await enhance_narrative(state)
    assert knowledge_result2["next"] is not None
    
    # Verify temporal connections
    first_pattern = narrative_patterns[0]
    second_pattern = narrative_patterns[1]
    assert datetime.fromisoformat(second_pattern["timestamp"]) > datetime.fromisoformat(first_pattern["timestamp"])
    
    return state

@pytest.mark.asyncio
async def test_narrative_pattern_detection(mock_llm):
    """Test narrative pattern detection and analysis."""
    state = GonzoState()
    state.messages.current_message = """
    The way these tech companies are implementing AI reminds me of the early days 
    of social media manipulation. The same promises of 'democratization' while 
    building walled gardens of control. From the Summer of Love to the Winter of AI, 
    the song remains the same - just with better special effects.
    """
    
    # Run narrative analysis
    result = await analyze_narrative(state, mock_llm)
    
    # Verify analysis results
    assert result["next"] == "respond"
    assert len(state.analysis.patterns) > 0
    
    # Check pattern content
    latest_pattern = state.analysis.patterns[-1]
    assert latest_pattern["type"] == "narrative"
    assert isinstance(latest_pattern["content"], str)
    assert len(latest_pattern["content"]) > 0
    
    return state

@pytest.mark.asyncio
async def test_narrative_error_handling(mock_llm):
    """Test error handling in narrative analysis."""
    state = GonzoState()
    state.messages.current_message = None  # Should trigger error handling
    
    # Run analysis with invalid state
    result = await analyze_narrative(state, mock_llm)
    
    # Verify error handling
    assert result["next"] == "error"
    
    return state