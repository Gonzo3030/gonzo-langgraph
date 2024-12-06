"""Core workflow definition for the Gonzo agent.

This module defines the main graph structure that enables Gonzo to:
1. Analyze current events through the lens of preventing a dystopian future
2. Connect patterns across different domains (politics, economics, media)
3. Educate and awaken people to manipulation and control systems
4. Maintain the authentic voice of the original "Brown Buffalo"
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, Graph, END
from ..types import GonzoState
from ..nodes.core import AssessmentNode
from ..nodes.core.analysis import MarketAnalysisNode, NarrativeAnalysisNode, CausalityAnalysisNode

def create_workflow() -> Graph:
    """Create the Gonzo agent workflow graph using enhanced node structure."""
    # Initialize workflow
    workflow = StateGraph(GonzoState)
    
    # Initialize nodes
    assessment = AssessmentNode()
    market_analysis = MarketAnalysisNode()
    narrative_analysis = NarrativeAnalysisNode()
    causality_analysis = CausalityAnalysisNode()
    
    # Add nodes to graph
    workflow.add_node("assessment", assessment.process)
    workflow.add_node("market_analysis", market_analysis.process)
    workflow.add_node("narrative_analysis", narrative_analysis.process)
    workflow.add_node("causality_analysis", causality_analysis.process)
    
    # Define routing logic
    def route_after_assessment(state: GonzoState) -> str:
        """Route to appropriate analysis node based on state assessment."""
        # Extract routing information
        category = state.get("category", "")
        requires_market = state.get("requires_market_analysis", False)
        requires_narrative = state.get("requires_narrative_analysis", False)
        requires_causality = state.get("requires_causality_analysis", False)
        
        # Priority routing based on state flags
        if requires_causality:
            return "causality_analysis"
        elif requires_market:
            return "market_analysis"
        elif requires_narrative:
            return "narrative_analysis"
            
        # Fallback routing based on category
        if category == "market":
            return "market_analysis"
        elif category == "narrative":
            return "narrative_analysis"
        
        return END
    
    def route_after_analysis(state: GonzoState) -> str:
        """Route after analysis completion."""
        # For now, end after analysis
        return END
    
    # Add conditional edges with correct pathing
    workflow.add_conditional_edges(
        "assessment",
        route_after_assessment,
        {
            "market_analysis": "market_analysis",
            "narrative_analysis": "narrative_analysis",
            "causality_analysis": "causality_analysis",
            END: END
        }
    )
    
    # Add analysis completion edges
    for node in ["market_analysis", "narrative_analysis", "causality_analysis"]:
        workflow.add_conditional_edges(
            node,
            route_after_analysis,
            {END: END}
        )
    
    # Set entry point
    workflow.set_entry_point("assessment")
    
    return workflow.compile()