from typing import Dict, Any
from .base import BaseNode
from ...types import GonzoState

class AssessmentNode(BaseNode):
    """Initial assessment node that determines processing path.
    
    Analyzes input to determine:
    - Content category (crypto, narrative, etc)
    - Required analysis types
    - Potential manipulation markers
    - Historical context needs
    """
    
    def _process(self, state: GonzoState) -> GonzoState:
        """Process incoming state to determine next steps.
        
        Args:
            state: Current state with input message
            
        Returns:
            State updated with assessment results
        """
        # For now, just maintain existing state routing
        if not state.get('category'):
            # Default to market analysis if no category is set
            state['category'] = 'market'
            state['requires_market_analysis'] = True
            
        return state
        
    def validate_state(self, state: GonzoState) -> bool:
        """Ensure state has required message content."""
        return len(state.get('messages', [])) > 0