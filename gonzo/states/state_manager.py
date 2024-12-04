from typing import Dict, Any
from langgraph.graph import StateGraph
from . import (
    initial_assessment,
    crypto_analysis,
    narrative_detection,
    knowledge_integration,
    response_generation
)

class StateManager:
    """Manages state transitions and graph execution for the Gonzo agent."""
    
    def __init__(self):
        self.graph = StateGraph()
        self._initialize_nodes()
        self._setup_transitions()
    
    def _initialize_nodes(self):
        """Initialize all nodes."""
        # Add nodes to graph
        self.graph.add_node("initial", initial_assessment)
        self.graph.add_node("crypto", crypto_analysis)
        self.graph.add_node("narrative", narrative_detection)
        self.graph.add_node("knowledge", knowledge_integration)
        self.graph.add_node("response", response_generation)
    
    def _setup_transitions(self):
        """Setup state transitions."""
        # Define conditional router
        def next_step_router(state):
            if state.get("errors"):
                return "response"
            
            category = state.get("context", {}).get("category")
            if category == "crypto":
                return "crypto"
            elif category == "narrative":
                return "narrative"
            return "response"
        
        # Add edges with conditions
        self.graph.add_edge("initial", next_step_router)
        self.graph.add_edge("crypto", "response")
        self.graph.add_edge("narrative", "response")
        self.graph.add_edge("knowledge", "response")
        
        # Set entry point
        self.graph.set_entry_point("initial")
        
        # Compile graph
        self.compiled_graph = self.graph.compile()
    
    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the state machine with given initial state."""
        return self.compiled_graph.invoke(initial_state)