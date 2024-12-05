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