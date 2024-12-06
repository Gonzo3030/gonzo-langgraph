from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ...types import GonzoState
from langchain_core.runnables import RunnableConfig

class BaseNode(ABC):
    """Base class for all Gonzo graph nodes.
    
    Provides common functionality and enforces consistent interface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def invoke(self, state: GonzoState, config: Optional[RunnableConfig] = None, **kwargs: Any) -> GonzoState:
        """Synchronous processing of state.
        
        Args:
            state: Current GonzoState
            config: Optional runtime configuration
            
        Returns:
            Updated GonzoState
        """
        return self._process(state)
        
    async def ainvoke(self, state: GonzoState, config: Optional[RunnableConfig] = None, **kwargs: Any) -> GonzoState:
        """Asynchronous processing of state.
        
        Args:
            state: Current GonzoState
            config: Optional runtime configuration
            
        Returns:
            Updated GonzoState
        """
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