from typing import Dict, Any
from langgraph.graph import StateGraph
from .initial import InitialState
from .crypto import CryptoState
from .narrative import NarrativeState
from .knowledge import KnowledgeState
from .response import ResponseState

class StateManager:
    """Manages state transitions and graph execution for the Gonzo agent."""
    
    def __init__(self):
        self.graph = StateGraph()
        self._initialize_states()
        self._setup_transitions()
    
    def _initialize_states(self):
        """Initialize all states."""
        self.states = {
            'initial': InitialState(),
            'crypto': CryptoState(),
            'narrative': NarrativeState(),
            'knowledge': KnowledgeState(),
            'response': ResponseState()
        }
        
        # Add states to graph
        for name, state in self.states.items():
            self.graph.add_node(name, state.run)
    
    def _setup_transitions(self):
        """Setup state transitions."""
        # From initial state
        self.graph.add_edge('initial', 'crypto')
        self.graph.add_edge('initial', 'narrative')
        self.graph.add_edge('initial', 'knowledge')
        
        # To response state
        self.graph.add_edge('crypto', 'response')
        self.graph.add_edge('narrative', 'response')
        self.graph.add_edge('knowledge', 'response')
        
        # Compile graph
        self.compiled_graph = self.graph.compile()
    
    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the state machine with given initial state."""
        return self.compiled_graph.run(initial_state)