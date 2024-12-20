from typing import Dict, Any, Optional
from langgraph.graph import StateGraph
from langsmith.run_trees import RunTree
from . import (
    initial_assessment,
    crypto_analysis,
    narrative_detection,
    knowledge_integration,
    response_generation
)

class StateManager:
    """Enhanced state manager with LangSmith tracking and batch processing."""
    
    def __init__(self, run_tree: Optional[RunTree] = None):
        self.graph = StateGraph()
        self.run_tree = run_tree
        self._initialize_nodes()
        self._setup_transitions()
        
    def _initialize_nodes(self):
        """Initialize all nodes with tracking."""
        # Add nodes to graph with tracking
        for name, node in [
            ("initial", initial_assessment),
            ("crypto", crypto_analysis),
            ("narrative", narrative_detection),
            ("knowledge", knowledge_integration),
            ("response", response_generation)
        ]:
            if hasattr(node, 'set_run_tree'):
                node.set_run_tree(self.run_tree)
            self.graph.add_node(name, node)
    
    def _setup_transitions(self):
        """Setup state transitions with tracking."""
        def next_step_router(state: Dict[str, Any]) -> str:
            """Route to next state based on current state and batch processing results."""
            if self.run_tree:
                with self.run_tree.as_child('state_transition') as run:
                    run.update_inputs({'current_state': state})
                    next_state = self._determine_next_state(state)
                    run.update_outputs({'next_state': next_state})
                    return next_state
            return self._determine_next_state(state)
        
        # Add edges with conditional routing
        self.graph.add_edge("initial", next_step_router)
        self.graph.add_edge("crypto", "response")
        self.graph.add_edge("narrative", "response")
        self.graph.add_edge("knowledge", "response")
        
        # Set entry point
        self.graph.set_entry_point("initial")
        
        # Compile graph
        self.compiled_graph = self.graph.compile()
    
    def _determine_next_state(self, state: Dict[str, Any]) -> str:
        """Determine the next state based on current state and processing results."""
        # Check for errors first
        if state.get("errors"):
            return "response"
        
        # Get category and batch processing results
        category = state.get("context", {}).get("category")
        batch_results = state.get("current_batch", {})
        
        # Use batch processing results to influence routing
        if batch_results:
            similarity_score = batch_results.get("similarity_score", 0)
            if similarity_score > 0.8:  # High similarity suggests related events
                if category == "crypto":
                    return "crypto"
                elif category == "narrative":
                    return "narrative"
        
        # Default to knowledge integration for mixed or uncertain cases
        return "knowledge"
    
    async def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the state machine with given initial state and tracking."""
        if self.run_tree:
            with self.run_tree.as_child('graph_execution') as run:
                run.update_inputs({'initial_state': initial_state})
                final_state = await self.compiled_graph.ainvoke(initial_state)
                run.update_outputs({'final_state': final_state})
                return final_state
        return await self.compiled_graph.ainvoke(initial_state)