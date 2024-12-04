import pytest
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from gonzo.nodes.narrative import analyze_narrative
from gonzo.types import GonzoState, create_initial_state

def test_narrative_analysis_basic():
    # Arrange
    initial_state = create_initial_state(
        HumanMessage(content="The media keeps saying inflation is transitory and the economy is doing great, "  
                    "but why do I feel poorer every day?")
    )
    
    # Act
    updates = analyze_narrative(initial_state)
    
    # Print analysis for inspection
    print("\nGonzo Analysis (Basic):\n" + "=" * 50)
    print(updates["response"])
    print("=" * 50 + "\n")
    
    # Assert
    assert "gonzo_analysis" in updates["context"]
    assert len(updates["context"]["gonzo_analysis"]) > 100  # Should be a substantial analysis
    assert updates["steps"][0]["node"] == "narrative_analysis"
    assert "raw_analysis" in updates["steps"][0]
    assert updates["response"].startswith('🔥')  # Fire emoji

def test_narrative_analysis_propaganda():
    # Arrange
    initial_state = create_initial_state(
        HumanMessage(content="Big tech companies say they need to collect our data to 'improve user experience' " 
                    "and 'provide better services'. Is this the whole story?")
    )
    
    # Act
    updates = analyze_narrative(initial_state)
    
    # Print analysis for inspection
    print("\nGonzo Analysis (Propaganda):\n" + "=" * 50)
    print(updates["response"])
    print("=" * 50 + "\n")
    
    analysis = updates["context"]["gonzo_analysis"]
    
    # Assert - Check for Gonzo style markers
    analysis_lower = analysis.lower()
    # Should contain critique of power structures
    assert any(term in analysis_lower for term in ["corporate", "power", "control", "profit", "surveillance"])
    # Should be substantial
    assert len(analysis) > 200
    # Should maintain Gonzo voice - check for style markers
    gonzo_markers = ["!", "*", "-", "..."]
    assert any(term in analysis for term in gonzo_markers), f"No Gonzo style markers found. Looking for: {gonzo_markers}"

def test_narrative_analysis_error_handling():
    # Arrange - create invalid state
    invalid_state = create_initial_state("")
    invalid_state["messages"] = []
    
    # Act
    updates = analyze_narrative(invalid_state)
    
    # Assert
    assert "narrative_error" in updates["context"]
    assert len(updates["steps"]) == 1
    assert "error" in updates["steps"][0]
    assert "bad trips" in updates["response"].lower()  # Check for Gonzo-style error message