"""
Core workflow definition for the Gonzo agent.

This module defines the main graph structure that enables Gonzo to:
1. Analyze current events through the lens of preventing a dystopian future
2. Connect patterns across different domains (politics, economics, media)
3. Educate and awaken people to manipulation and control systems
4. Maintain the authentic voice of the original "Brown Buffalo"
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, Graph
from ..types import GonzoState
from ..nodes.assessment import assess_input
from ..nodes.analysis import (
    analyze_market_data,
    analyze_narrative,
    analyze_causality,
    detect_manipulation
)
from ..nodes.memory import (
    update_historical_context,
    check_pattern_database
)
from ..nodes.response import (
    generate_gonzo_response,
    validate_voice_authenticity
)

def create_workflow() -> Graph:
    """Create the Gonzo agent workflow graph with sophisticated state management."""
    workflow = StateGraph(GonzoState)
    
    # Add Core Analysis Nodes
    workflow.add_node("assessment", assess_input)
    workflow.add_node("market_analysis", analyze_market_data)
    workflow.add_node("narrative_analysis", analyze_narrative)
    workflow.add_node("causality_analysis", analyze_causality)
    workflow.add_node("manipulation_detection", detect_manipulation)
    
    # Add Memory Management Nodes
    workflow.add_node("pattern_check", check_pattern_database)
    workflow.add_node("update_history", update_historical_context)
    
    # Add Response Generation Nodes
    workflow.add_node("generate_response", generate_gonzo_response)
    workflow.add_node("voice_validation", validate_voice_authenticity)
    
    # Define Sophisticated Routing Logic
    def route_next(state: GonzoState) -> str:
        """
        Route to next node based on state analysis and mission requirements.
        """
        # Extract key state information
        category = state["category"]
        confidence = state.get("confidence", 0.0)
        manipulation_detected = state.get("manipulation_detected", False)
        requires_historical = state.get("requires_historical", False)
        
        # Priority routing for manipulation detection
        if manipulation_detected:
            return "manipulation_detection"
            
        # Route based on category with integrated pattern checking
        if category == "crypto":
            return "market_analysis"
        elif category == "narrative":
            return "narrative_analysis"
        elif category == "causality":
            return "causality_analysis"
            
        # Default to response generation
        return "generate_response"

    def route_after_analysis(state: GonzoState) -> str:
        """
        Determine next steps after initial analysis.
        """
        if state.get("requires_pattern_check", False):
            return "pattern_check"
        elif state.get("requires_historical_update", False):
            return "update_history"
        return "generate_response"

    def route_final(state: GonzoState) -> str:
        """
        Final routing before response generation.
        """
        if not state.get("voice_validated", False):
            return "voice_validation"
        return "end"
    
    # Add Primary Analysis Edges
    workflow.add_edge("assessment", route_next)
    workflow.add_edge("market_analysis", route_after_analysis)
    workflow.add_edge("narrative_analysis", route_after_analysis)
    workflow.add_edge("causality_analysis", route_after_analysis)
    workflow.add_edge("manipulation_detection", route_after_analysis)
    
    # Add Memory Management Edges
    workflow.add_edge("pattern_check", "generate_response")
    workflow.add_edge("update_history", "generate_response")
    
    # Add Response Generation Edges
    workflow.add_edge("generate_response", route_final)
    workflow.add_edge("voice_validation", "end")
    
    # Set entry point
    workflow.set_entry_point("assessment")
    
    # Compile graph
    return workflow.compile()
