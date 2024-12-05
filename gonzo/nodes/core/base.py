from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ...types import GonzoState

class BaseNode(ABC):
    """Base class for all Gonzo graph nodes.
    
    Provides common functionality and enforces consistent interface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
    @abstractmethod
    async def process(self, state: GonzoState) -> GonzoState:
        """Process the current state and return updated state.
        
        Args:
            state: Current GonzoState
            
        Returns:
            Updated GonzoState
        """
        pass
        
    def validate_state(self, state: GonzoState) -> bool:
        """Validate state contains required fields for this node.
        
        Args:
            state: State to validate
            
        Returns:
            bool: Whether state is valid
        """
        return True
        
    def get_state_updates(self, state: GonzoState) -> Dict[str, Any]:
        """Extract relevant updates from state.
        
        Args:
            state: Current state
            
        Returns:
            Dict of updates to apply
        """
        return {}