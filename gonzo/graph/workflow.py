from typing import Dict, Any, TypeVar, Annotated, Sequence
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..types import GonzoState
from ..nodes.knowledge_enhanced_assessment import enhance_assessment
from ..nodes.knowledge_enhanced_narrative import enhance_narrative

StateType = TypeVar("StateType", bound=BaseModel)

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow graph."""
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("assessment", enhance_assessment)
    workflow.add_node("narrative", enhance_narrative)
    
    # Define edge conditions
    @workflow.conditional_edge_handler
    def route_assessment(state: GonzoState) -> Sequence[str]:
        """Route state after assessment."""
        if state.next_step == "narrative":
            return ["narrative"]
        return [END]
    
    # Add edges
    workflow.add_conditional_edges(
        "assessment",
        route_assessment
    )
    
    workflow.add_edge("narrative", END)
    
    # Set entry point
    workflow.set_entry_point("assessment")
    
    return workflow.compile()