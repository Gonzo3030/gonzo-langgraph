from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from langchain_core.runnables import Runnable, RunnableConfig
from ...types import GonzoState

class BaseNode(Runnable[GonzoState, GonzoState], ABC):
    """Base class for all Gonzo graph nodes.
    
    Inherits from Runnable to properly integrate with LangGraph.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
    
    def invoke(self, state: GonzoState, config: Optional[RunnableConfig] = None, **kwargs: Any) -> GonzoState:
        """Synchronous processing of state.
        
        Args:
            state: Current GonzoState
            config: Optional runtime configuration
            
        Returns:
            Updated GonzoState
        """
        # Validate state before processing
        if not self.validate_state(state):
            return state
            
        return self._process(state)
        
    async def ainvoke(self, state: GonzoState, config: Optional[RunnableConfig] = None, **kwargs: Any) -> GonzoState:
        """Asynchronous processing of state.
        
        Args:
            state: Current GonzoState
            config: Optional runtime configuration
            
        Returns:
            Updated GonzoState
        """
        # Validate state before processing
        if not self.validate_state(state):
            return state
            
        return self._process(state)
    
    @abstractmethod
    def _process(self, state: GonzoState) -> GonzoState:
        """Core processing logic to be implemented by subclasses.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
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