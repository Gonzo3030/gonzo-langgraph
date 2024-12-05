from typing import Dict, Any
from langgraph.graph import StateGraph, Graph
from ..types import GonzoState
from ..nodes.core import AssessmentNode, AnalysisNode
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
    def route_next(state: GonzoState) -> str:
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
        
        return "end"
    
    # Add edges with conditional routing
    workflow.add_edge("assessment", route_next)
    workflow.add_edge("market_analysis", route_next)
    workflow.add_edge("narrative_analysis", route_next)
    workflow.add_edge("causality_analysis", route_next)
    
    # Set entry point
    workflow.set_entry_point("assessment")
    
    return workflow.compile()
