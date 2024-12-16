"""Main workflow definition for Gonzo."""

from typing import Dict, Any
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from .types import GonzoState, NextStep
from .nodes.pattern_detection import detect_patterns
from .nodes.narrative import analyze_narrative
from .nodes.assessment import assess_input
from .config import ANTHROPIC_MODEL, MODEL_CONFIG

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow."""
    # Initialize LLM
    llm = ChatAnthropic(
        model=ANTHROPIC_MODEL,
        **MODEL_CONFIG
    )
    
    # Initialize the graph
    workflow = StateGraph(GonzoState)
    
    # Add nodes
    workflow.add_node("assessment", lambda state: assess_input(state))
    workflow.add_node("pattern_detection", lambda state: detect_patterns(state, llm))
    workflow.add_node("narrative", lambda state: analyze_narrative(state))
    
    # Define edges based on state.next_step
    workflow.add_edge("assessment", _get_next_step)
    workflow.add_edge("pattern_detection", _get_next_step)
    workflow.add_edge("narrative", _get_next_step)
    
    # Set entry point
    workflow.set_entry_point("assessment")
    
    return workflow.compile()

def _get_next_step(state: Dict[str, Any]) -> str:
    """Determine next step based on state."""
    try:
        return state.get("next_step", NextStep.END)
    except Exception as e:
        print(f"Error determining next step: {str(e)}")
        return NextStep.END