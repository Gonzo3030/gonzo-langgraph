from typing import Dict, Any, TypeVar, Optional
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
    
    # Define conditional edges
    def should_route_to_narrative(state: GonzoState) -> str:
        if state.next_step == "narrative":
            return "narrative"
        elif state.next_step == "error":
            return END
        else:
            return END

    # Add edges
    workflow.add_edge("assessment", should_route_to_narrative)
    workflow.add_edge("narrative", END)
    
    # Set entry point
    workflow.set_entry_point("assessment")
    
    return workflow.compile()