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
    
    # Assert
    assert "narrative_analysis" in updates["context"]
    assert "steps" in updates
    assert "response" in updates
    
    analysis = updates["context"]["narrative_analysis"]
    assert "propaganda_techniques" in analysis
    assert "primary_beneficiaries" in analysis
    assert "counter_narratives" in analysis
    assert "manipulation_tactics" in analysis
    assert "societal_impact" in analysis
    assert "gonzo_perspective" in analysis

def test_narrative_analysis_propaganda():
    # Arrange
    initial_state = create_initial_state(
        HumanMessage(content="Big tech companies say they need to collect our data to 'improve user experience' " 
                    "and 'provide better services'. Is this the whole story?")
    )
    
    # Act
    updates = analyze_narrative(initial_state)
    analysis = updates["context"]["narrative_analysis"]
    
    # Assert
    assert len(analysis["propaganda_techniques"]) > 0
    assert len(analysis["primary_beneficiaries"]) > 0
    assert len(analysis["counter_narratives"]) > 0
    assert len(analysis["manipulation_tactics"]) > 0
    assert analysis["societal_impact"].strip() != ""
    assert analysis["gonzo_perspective"].strip() != ""

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
    assert updates["response"].startswith("Error")
